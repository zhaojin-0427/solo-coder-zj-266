from datetime import date, datetime
from collections import Counter
from django.db.models import Avg
from ..models import (
    Customer, NailWork, Appointment, CustomerPreference,
    RiskScoreHistory
)
from .scoring import (
    score_visit_recency, score_cancel_rate, score_satisfaction_drop,
    score_preference_match, score_duration_stability
)


def generate_followup_scripts(customer_name, final_score):
    if final_score >= 70:
        return [
            f'您好 {customer_name}，好久不见啦！最近有适合您的新款式到店，特别适合这个季节，想邀您来体验一下~',
            f'{customer_name}，您上次来已经有段时间啦，我们推出了会员专属优惠，老顾客还可以享受额外福利哦！',
        ], '紧急回访，建议本周内电话或微信联系，提供专属优惠或赠送小礼品'
    elif final_score >= 40:
        return [
            f'{customer_name} 您好，最近天气变化，记得照顾好自己哦~ 我们上新了几款非常适合您风格的款式，有空可以来看看！',
            f'{customer_name}，距离您上次到店有段时间了，想问问您之前做的指甲还满意吗？有任何问题随时可以过来免费修补~',
        ], '建议两周内联系，推送新款资讯和会员活动'
    else:
        return [
            f'{customer_name} 您好，非常感谢您一直以来的支持！最近我们有新款上新，随时欢迎您过来体验~',
        ], '正常维护，可在节日或活动时发送问候'


def calculate_churn_risk(customer):
    today = date.today()
    factors = {}
    total_score = 0
    max_score = 100
    reasons = []

    works = NailWork.objects.filter(customer=customer).order_by('-completed_at')
    appointments = Appointment.objects.filter(customer=customer)

    last_visit = works.first().completed_at if works.exists() else None
    if last_visit:
        days_since = (today - last_visit).days
        visit_score = score_visit_recency(days_since)
        factors['days_since_visit'] = days_since
        if days_since > 45:
            reasons.append(f'已 {days_since} 天未到店')
    else:
        visit_score = score_visit_recency(None)
        factors['days_since_visit'] = None
        reasons.append('暂无到店记录')
    total_score += visit_score * 0.35

    cancel_count = appointments.filter(status='cancelled').count()
    total_appt = appointments.count()
    cancel_rate = (cancel_count / total_appt * 100) if total_appt > 0 else 0
    cancel_score = score_cancel_rate(cancel_count, total_appt)
    factors['cancel_count'] = cancel_count
    factors['cancel_rate'] = round(cancel_rate, 1)
    if cancel_count >= 2:
        reasons.append(f'累计取消 {cancel_count} 次预约（取消率 {cancel_rate:.0f}%）')
    total_score += cancel_score * 0.2

    if works.count() >= 2:
        recent_works = list(works[:3])
        older_works = list(works[3:6]) if works.count() > 3 else list(works[1:3])
        if recent_works and older_works:
            recent_avg = sum(w.satisfaction for w in recent_works) / len(recent_works)
            older_avg = sum(w.satisfaction for w in older_works) / len(older_works)
            satisfaction_drop = older_avg - recent_avg
            sat_score = score_satisfaction_drop(satisfaction_drop)
            factors['recent_avg_satisfaction'] = round(recent_avg, 2)
            factors['older_avg_satisfaction'] = round(older_avg, 2)
            factors['satisfaction_drop'] = round(satisfaction_drop, 2)
            if satisfaction_drop >= 0.5:
                reasons.append(f'满意度下降 {satisfaction_drop:.1f} 星（{older_avg:.1f} → {recent_avg:.1f}）')
        else:
            sat_score = 0
    else:
        sat_score = 10
        factors['recent_avg_satisfaction'] = None
    total_score += sat_score * 0.2

    if works.count() >= 3:
        try:
            pref, _ = CustomerPreference.objects.get_or_create(customer=customer)
            pref_colors = set(c.strip() for c in pref.preferred_colors.split(',') if c.strip())
            pref_styles = set(s.strip() for s in pref.preferred_styles.split(',') if s.strip())
            recent_works_color = Counter()
            recent_works_style = Counter()
            for w in works[:3]:
                if w.actual_color:
                    recent_works_color[w.actual_color] += 1
                if w.design:
                    for t in w.design.style_tags.all():
                        recent_works_style[t.name] += 1
            color_match = any(c in pref_colors for c in recent_works_color.keys()) if pref_colors else True
            style_match = any(s in pref_styles for s in recent_works_style.keys()) if pref_styles else True
            pref_score = score_preference_match(color_match, style_match)
            if pref_score == 40:
                reasons.append('近期作品偏好与登记偏好差异较大')
            factors['pref_color_match'] = color_match
            factors['pref_style_match'] = style_match
        except Exception:
            pref_score = 0
    else:
        pref_score = 0
    total_score += pref_score * 0.15

    if works.exists():
        avg_duration = works.aggregate(avg=Avg('duration_days'))['avg'] or 0
        dur_score = score_duration_stability(avg_duration)
        factors['avg_duration_days'] = round(avg_duration, 1)
        if avg_duration < 20:
            reasons.append(f'作品平均维持仅 {avg_duration:.0f} 天，低于正常水平')
    else:
        dur_score = 10
    total_score += dur_score * 0.1

    final_score = round(min(total_score, max_score), 1)
    if final_score >= 70:
        risk_level = 'high'
        risk_label = '高风险'
    elif final_score >= 40:
        risk_level = 'medium'
        risk_label = '中风险'
    else:
        risk_level = 'low'
        risk_label = '低风险'

    scripts, action_text = generate_followup_scripts(customer.name, final_score)

    customer.churn_risk_score = final_score
    customer.recommended_action = action_text
    customer.save()

    RiskScoreHistory.objects.create(
        customer=customer,
        score=final_score,
        factors={**factors, 'reasons': reasons}
    )

    return {
        'score': final_score,
        'risk_level': risk_level,
        'risk_label': risk_label,
        'reasons': reasons,
        'factors': factors,
        'scripts': scripts,
        'recommended_action': action_text,
    }


def get_high_risk_customers(threshold=40):
    from ..serializers import CustomerSerializer
    results = []
    for customer in Customer.objects.all():
        risk = calculate_churn_risk(customer)
        if risk['score'] >= threshold:
            cust_data = CustomerSerializer(customer).data
            cust_data['risk_score'] = risk['score']
            cust_data['risk_level'] = risk['risk_level']
            cust_data['risk_label'] = risk['risk_label']
            cust_data['risk_reasons'] = risk['reasons']
            cust_data['scripts'] = risk['scripts']
            cust_data['recommended_action'] = risk['recommended_action']
            results.append(cust_data)
    results.sort(key=lambda x: x['risk_score'], reverse=True)
    return results
