from django.db import models
from datetime import date, datetime


class Technician(models.Model):
    name = models.CharField(max_length=100, verbose_name='姓名')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    avatar = models.ImageField(upload_to='technicians/', blank=True, null=True, verbose_name='头像')
    specialty = models.CharField(max_length=200, blank=True, verbose_name='专长')
    hire_date = models.DateField(default=date.today, verbose_name='入职日期')
    is_active = models.BooleanField(default=True, verbose_name='在职')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '美甲师'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return self.name


class Customer(models.Model):
    GENDER_CHOICES = [
        ('female', '女'),
        ('male', '男'),
        ('other', '其他'),
    ]
    MEMBER_LEVEL_CHOICES = [
        ('normal', '普通会员'),
        ('silver', '银卡会员'),
        ('gold', '金卡会员'),
        ('platinum', '钻石会员'),
    ]
    name = models.CharField(max_length=100, verbose_name='姓名')
    phone = models.CharField(max_length=20, unique=True, verbose_name='手机号')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='female', verbose_name='性别')
    birthday = models.DateField(blank=True, null=True, verbose_name='生日')
    avatar = models.ImageField(upload_to='customers/', blank=True, null=True, verbose_name='头像')
    notes = models.TextField(blank=True, verbose_name='备注')
    member_level = models.CharField(max_length=20, choices=MEMBER_LEVEL_CHOICES, default='normal', verbose_name='会员等级')
    last_contact_at = models.DateTimeField(blank=True, null=True, verbose_name='最近联系时间')
    churn_risk_score = models.FloatField(default=0, verbose_name='流失风险评分')
    recommended_action = models.TextField(blank=True, verbose_name='推荐跟进动作')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '顾客'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return f'{self.name} ({self.phone})'


class StyleTag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='风格名称')
    color = models.CharField(max_length=7, default='#6366f1', verbose_name='标签颜色')

    class Meta:
        verbose_name = '风格标签'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self):
        return self.name


class NailDesign(models.Model):
    NAIL_SHAPE_CHOICES = [
        ('oval', '椭圆形'),
        ('square', '方形'),
        ('squoval', '方圆形'),
        ('almond', '杏仁形'),
        ('stiletto', '尖形'),
        ('coffin', '棺材形'),
        ('ballerina', '芭蕾舞形'),
        ('round', '圆形'),
    ]
    OCCASION_CHOICES = [
        ('daily', '日常'),
        ('wedding', '婚礼'),
        ('party', '派对'),
        ('office', '职场'),
        ('festival', '节日'),
        ('travel', '旅行'),
        ('date', '约会'),
    ]

    name = models.CharField(max_length=200, verbose_name='款式名称')
    image = models.ImageField(upload_to='designs/', verbose_name='款式图片')
    nail_shape = models.CharField(max_length=20, choices=NAIL_SHAPE_CHOICES, verbose_name='甲型')
    color_system = models.CharField(max_length=100, verbose_name='色系')
    decoration = models.CharField(max_length=300, verbose_name='装饰元素')
    occasion = models.CharField(max_length=20, choices=OCCASION_CHOICES, verbose_name='适用场合')
    style_tags = models.ManyToManyField(StyleTag, blank=True, verbose_name='风格标签')
    description = models.TextField(blank=True, verbose_name='描述')
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='上传美甲师', related_name='designs')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='参考价格')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '美甲款式'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def auto_assign_style_tags(self):
        tags_to_add = []
        color_lower = self.color_system.lower()
        dec_lower = self.decoration.lower()

        if any(k in color_lower for k in ['粉', '红', '玫瑰']):
            tag, _ = StyleTag.objects.get_or_create(name='甜美', defaults={'color': '#ec4899'})
            tags_to_add.append(tag)
        if any(k in color_lower for k in ['黑', '暗', '深']):
            tag, _ = StyleTag.objects.get_or_create(name='酷飒', defaults={'color': '#6b7280'})
            tags_to_add.append(tag)
        if any(k in color_lower for k in ['白', '裸', '米']):
            tag, _ = StyleTag.objects.get_or_create(name='简约', defaults={'color': '#f59e0b'})
            tags_to_add.append(tag)
        if any(k in dec_lower for k in ['闪', '钻', '亮片', '珠']):
            tag, _ = StyleTag.objects.get_or_create(name='奢华', defaults={'color': '#a855f7'})
            tags_to_add.append(tag)
        if any(k in dec_lower for k in ['花', '手绘', '卡通', '图案']):
            tag, _ = StyleTag.objects.get_or_create(name='艺术', defaults={'color': '#10b981'})
            tags_to_add.append(tag)
        if any(k in color_lower for k in ['蓝', '绿', '清', '淡']):
            tag, _ = StyleTag.objects.get_or_create(name='清新', defaults={'color': '#06b6d4'})
            tags_to_add.append(tag)
        if self.occasion == 'wedding':
            tag, _ = StyleTag.objects.get_or_create(name='新娘', defaults={'color': '#f43f5e'})
            tags_to_add.append(tag)
        if self.occasion == 'festival':
            tag, _ = StyleTag.objects.get_or_create(name='节日', defaults={'color': '#ef4444'})
            tags_to_add.append(tag)

        if not tags_to_add:
            tag, _ = StyleTag.objects.get_or_create(name='经典', defaults={'color': '#6366f1'})
            tags_to_add.append(tag)

        self.style_tags.set(tags_to_add)


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='顾客',
                                 related_name='appointments')
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, verbose_name='美甲师',
                                   related_name='appointments')
    design = models.ForeignKey(NailDesign, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name='预约款式', related_name='appointments')
    appointment_date = models.DateField(verbose_name='预约日期')
    appointment_time = models.TimeField(verbose_name='预约时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '预约'
        verbose_name_plural = verbose_name
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f'{self.customer.name} - {self.appointment_date}'


class NailWork(models.Model):
    SATISFACTION_CHOICES = [
        (1, '非常不满意'),
        (2, '不满意'),
        (3, '一般'),
        (4, '满意'),
        (5, '非常满意'),
    ]

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='work',
                                       verbose_name='关联预约', null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='顾客',
                                 related_name='works')
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, verbose_name='操作美甲师',
                                   related_name='works')
    design = models.ForeignKey(NailDesign, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name='参考款式')
    photo = models.ImageField(upload_to='works/', verbose_name='完成照片', null=True, blank=True)
    actual_nail_shape = models.CharField(max_length=50, blank=True, verbose_name='实际甲型')
    actual_color = models.CharField(max_length=100, blank=True, verbose_name='实际色系')
    duration_days = models.IntegerField(default=0, verbose_name='维持天数')
    satisfaction = models.IntegerField(choices=SATISFACTION_CHOICES, default=5, verbose_name='满意度')
    customer_feedback = models.TextField(blank=True, verbose_name='顾客反馈')
    completed_at = models.DateField(default=date.today, verbose_name='完成日期')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '作品存档'
        verbose_name_plural = verbose_name
        ordering = ['-completed_at']

    def __str__(self):
        return f'{self.customer.name} - {self.completed_at}'


class CustomerPreference(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, verbose_name='顾客',
                                    related_name='preference')
    preferred_colors = models.CharField(max_length=500, blank=True, verbose_name='偏好色系')
    preferred_shapes = models.CharField(max_length=200, blank=True, verbose_name='偏好甲型')
    preferred_styles = models.CharField(max_length=200, blank=True, verbose_name='偏好风格')
    preferred_occasions = models.CharField(max_length=200, blank=True, verbose_name='偏好场合')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '顾客偏好'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.customer.name}的偏好'


class ContactRecord(models.Model):
    CONTACT_TYPE_CHOICES = [
        ('phone', '电话'),
        ('wechat', '微信'),
        ('sms', '短信'),
        ('visit', '到店'),
        ('other', '其他'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='顾客',
                                 related_name='contact_records')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES, default='wechat',
                                    verbose_name='联系方式')
    content = models.TextField(verbose_name='联系内容')
    contacted_at = models.DateTimeField(default=datetime.now, verbose_name='联系时间')
    operator = models.CharField(max_length=50, blank=True, verbose_name='操作人')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '联系记录'
        verbose_name_plural = verbose_name
        ordering = ['-contacted_at']

    def __str__(self):
        return f'{self.customer.name} - {self.get_contact_type_display()}'


class RiskScoreHistory(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='顾客',
                                 related_name='risk_histories')
    score = models.FloatField(verbose_name='风险评分')
    factors = models.JSONField(default=dict, verbose_name='评分因子详情')
    recorded_at = models.DateTimeField(default=datetime.now, verbose_name='记录时间')

    class Meta:
        verbose_name = '风险评分历史'
        verbose_name_plural = verbose_name
        ordering = ['-recorded_at']

    def __str__(self):
        return f'{self.customer.name} - {self.score:.1f}分'


class TryOnTask(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '识别中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    SKIN_TONE_CHOICES = [
        ('fair', '冷白肤色'),
        ('light', '白皙肤色'),
        ('medium', '自然肤色'),
        ('tan', '小麦肤色'),
        ('dark', '健康肤色'),
    ]

    HAND_SHAPE_CHOICES = [
        ('slender', '纤细修长型'),
        ('standard', '标准匀称型'),
        ('plump', '丰满圆润型'),
        ('broad', '宽厚有力型'),
    ]

    NAIL_LENGTH_CHOICES = [
        ('very_short', '超短（<1mm）'),
        ('short', '短（1-3mm）'),
        ('medium', '中（3-6mm）'),
        ('long', '长（6-10mm）'),
        ('very_long', '超长（>10mm）'),
    ]

    BUDGET_CHOICES = [
        ('low', '平价（100元以下）'),
        ('medium', '中档（100-300元）'),
        ('high', '高档（300-600元）'),
        ('luxury', '奢华（600元以上）'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='顾客',
                                 related_name='try_on_tasks', null=True, blank=True)
    photo = models.ImageField(upload_to='try_on/', verbose_name='手部照片', null=True, blank=True)
    reference_work = models.ForeignKey(NailWork, on_delete=models.SET_NULL, verbose_name='参考历史作品',
                                       null=True, blank=True, related_name='referenced_by_try_ons')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    skin_tone = models.CharField(max_length=20, choices=SKIN_TONE_CHOICES, blank=True, verbose_name='识别肤色')
    hand_shape = models.CharField(max_length=20, choices=HAND_SHAPE_CHOICES, blank=True, verbose_name='识别手型')
    nail_length = models.CharField(max_length=20, choices=NAIL_LENGTH_CHOICES, blank=True, verbose_name='识别指甲长度')
    target_occasion = models.CharField(max_length=20, choices=NailDesign.OCCASION_CHOICES, blank=True, verbose_name='目标场合')
    budget = models.CharField(max_length=20, choices=BUDGET_CHOICES, blank=True, verbose_name='预算范围')
    preferred_colors = models.CharField(max_length=500, blank=True, verbose_name='偏好色系（多选，逗号分隔）')
    analysis_details = models.JSONField(default=dict, verbose_name='分析详情')
    converted_appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, verbose_name='转化预约',
                                              null=True, blank=True, related_name='source_try_on')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '试甲任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        cust_name = self.customer.name if self.customer else '未登录顾客'
        return f'{cust_name} - {self.get_status_display()} ({self.created_at.strftime("%m-%d %H:%M")})'


class SimilarDesignResult(models.Model):
    try_on_task = models.ForeignKey(TryOnTask, on_delete=models.CASCADE, verbose_name='试甲任务',
                                    related_name='similar_results')
    design = models.ForeignKey(NailDesign, on_delete=models.CASCADE, verbose_name='匹配款式',
                               related_name='similar_matches')
    similarity_score = models.FloatField(default=0, verbose_name='相似度评分（0-100）')
    shape_score = models.FloatField(default=0, verbose_name='甲型匹配分')
    color_score = models.FloatField(default=0, verbose_name='色系匹配分')
    decoration_score = models.FloatField(default=0, verbose_name='装饰匹配分')
    style_score = models.FloatField(default=0, verbose_name='风格匹配分')
    occasion_score = models.FloatField(default=0, verbose_name='场合匹配分')
    satisfaction_score = models.FloatField(default=0, verbose_name='历史满意度分')
    budget_score = models.FloatField(default=0, verbose_name='预算匹配分')
    score_breakdown = models.JSONField(default=dict, verbose_name='评分分解')
    rank = models.IntegerField(default=0, verbose_name='推荐排序')
    is_viewed = models.BooleanField(default=False, verbose_name='是否被浏览')
    viewed_at = models.DateTimeField(null=True, blank=True, verbose_name='浏览时间')

    class Meta:
        verbose_name = '相似款式推荐结果'
        verbose_name_plural = verbose_name
        ordering = ['try_on_task', '-similarity_score']

    def __str__(self):
        return f'{self.try_on_task.id} - {self.design.name} ({self.similarity_score:.1f}分)'


class DesignClickLog(models.Model):
    try_on_task = models.ForeignKey(TryOnTask, on_delete=models.SET_NULL, verbose_name='关联试甲任务',
                                    null=True, blank=True, related_name='click_logs')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, verbose_name='点击顾客',
                                 null=True, blank=True, related_name='design_clicks')
    design = models.ForeignKey(NailDesign, on_delete=models.CASCADE, verbose_name='被点击款式',
                               related_name='click_logs')
    similar_result = models.ForeignKey(SimilarDesignResult, on_delete=models.SET_NULL, verbose_name='关联推荐结果',
                                       null=True, blank=True, related_name='clicks')
    click_type = models.CharField(max_length=30, default='view', verbose_name='点击类型',
                                  choices=[('view', '浏览'), ('compare', '对比'), ('favorite', '收藏'), ('book', '预约')])
    clicked_at = models.DateTimeField(default=datetime.now, verbose_name='点击时间')

    class Meta:
        verbose_name = '款式点击日志'
        verbose_name_plural = verbose_name
        ordering = ['-clicked_at']

    def __str__(self):
        return f'{self.design.name} - {self.get_click_type_display()}'
