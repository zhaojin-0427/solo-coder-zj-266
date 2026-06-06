import os
import sys
import django
from datetime import date, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nail_salon.settings')
django.setup()

from nail_app.models import (
    Technician, Customer, StyleTag, NailDesign,
    Appointment, NailWork, CustomerPreference
)


def run():
    if Technician.objects.exists():
        print('数据已存在，跳过初始化')
        return

    print('开始初始化数据...')

    technicians = [
        {'name': '小美', 'phone': '13800138001', 'specialty': '日式美甲、手绘', 'hire_date': date(2023, 1, 15)},
        {'name': '小丽', 'phone': '13800138002', 'specialty': '法式美甲、钻饰', 'hire_date': date(2023, 3, 20)},
        {'name': '小芳', 'phone': '13800138003', 'specialty': '光疗延长、雕花', 'hire_date': date(2023, 6, 10)},
        {'name': '小燕', 'phone': '13800138004', 'specialty': '欧美风、晕染', 'hire_date': date(2024, 1, 5)},
    ]
    tech_objs = []
    for t in technicians:
        tech_objs.append(Technician.objects.create(**t))

    print(f'  创建了 {len(tech_objs)} 个美甲师')

    customers = [
        {'name': '张小姐', 'phone': '13900139001', 'gender': 'female', 'birthday': date(1995, 5, 10)},
        {'name': '李女士', 'phone': '13900139002', 'gender': 'female', 'birthday': date(1988, 11, 22)},
        {'name': '王小姐', 'phone': '13900139003', 'gender': 'female', 'birthday': date(1998, 3, 8)},
        {'name': '赵女士', 'phone': '13900139004', 'gender': 'female', 'birthday': date(1992, 7, 15)},
        {'name': '陈小姐', 'phone': '13900139005', 'gender': 'female', 'birthday': date(2000, 9, 30)},
        {'name': '刘女士', 'phone': '13900139006', 'gender': 'female', 'birthday': date(1985, 2, 14)},
        {'name': '周小姐', 'phone': '13900139007', 'gender': 'female', 'birthday': date(1996, 12, 25)},
        {'name': '吴女士', 'phone': '13900139008', 'gender': 'female', 'birthday': date(1990, 6, 18)},
    ]
    cust_objs = []
    for c in customers:
        cust_objs.append(Customer.objects.create(**c))

    print(f'  创建了 {len(cust_objs)} 个顾客')

    style_tags = [
        ('甜美', '#ec4899'), ('酷飒', '#6b7280'), ('简约', '#f59e0b'),
        ('奢华', '#a855f7'), ('艺术', '#10b981'), ('清新', '#06b6d4'),
        ('新娘', '#f43f5e'), ('节日', '#ef4444'), ('经典', '#6366f1'),
    ]
    tag_objs = []
    for name, color in style_tags:
        tag_objs.append(StyleTag.objects.create(name=name, color=color))

    print(f'  创建了 {len(tag_objs)} 个风格标签')

    designs = [
        {'name': '樱花粉渐变', 'nail_shape': 'almond', 'color_system': '粉色系',
         'decoration': '樱花手绘、小珍珠', 'occasion': 'date', 'price': 268,
         'description': '温柔樱花粉渐变，搭配手绘樱花和精致小珍珠'},
        {'name': '法式裸色经典', 'nail_shape': 'squoval', 'color_system': '裸色系',
         'decoration': '法式白边、金线', 'occasion': 'office', 'price': 198,
         'description': '经典法式裸色，适合日常通勤'},
        {'name': '黑金奢华晚宴', 'nail_shape': 'coffin', 'color_system': '黑色系',
         'decoration': '金箔、水钻、链条', 'occasion': 'party', 'price': 388,
         'description': '神秘黑色配奢华金箔水钻，派对女王首选'},
        {'name': '冰透薄荷蓝', 'nail_shape': 'oval', 'color_system': '蓝色系',
         'decoration': '冰透效果、银箔碎片', 'occasion': 'daily', 'price': 228,
         'description': '清新冰透薄荷蓝，夏日清凉感'},
        {'name': '新娘白纱款', 'nail_shape': 'oval', 'color_system': '白色系',
         'decoration': '珍珠、碎钻、蕾丝手绘', 'occasion': 'wedding', 'price': 588,
         'description': '专为新娘设计的梦幻白色美甲'},
        {'name': '焦糖枫叶棕', 'nail_shape': 'square', 'color_system': '棕色系',
         'decoration': '枫叶手绘、金线条', 'occasion': 'daily', 'price': 258,
         'description': '秋日温暖焦糖棕，枫叶手绘增添氛围感'},
        {'name': '星河闪钻渐变', 'nail_shape': 'stiletto', 'color_system': '紫色系',
         'decoration': '闪粉渐变、大颗水钻', 'occasion': 'party', 'price': 358,
         'description': '神秘紫色渐变搭配星河闪钻'},
        {'name': '莫兰迪绿跳色', 'nail_shape': 'round', 'color_system': '绿色系',
         'decoration': '莫兰迪色系跳色、哑光', 'occasion': 'office', 'price': 208,
         'description': '高级莫兰迪绿，低调有质感'},
        {'name': '圣诞节日红', 'nail_shape': 'squoval', 'color_system': '红色系',
         'decoration': '雪花手绘、小铃铛、金粉', 'occasion': 'festival', 'price': 298,
         'description': '经典圣诞红，节日氛围感拉满'},
        {'name': '卡通手绘小熊', 'nail_shape': 'round', 'color_system': '奶茶色系',
         'decoration': '手绘小熊、奶油色', 'occasion': 'daily', 'price': 288,
         'description': '可爱手绘小熊，少女心满满'},
        {'name': '大理石晕染', 'nail_shape': 'coffin', 'color_system': '灰色系',
         'decoration': '大理石纹晕染、银箔', 'occasion': 'office', 'price': 278,
         'description': '高级感大理石纹，通勤必备'},
        {'name': '落日橘红晕染', 'nail_shape': 'almond', 'color_system': '橘色系',
         'decoration': '落日晕染、金箔点缀', 'occasion': 'travel', 'price': 248,
         'description': '温暖落日橘，度假风满满'},
    ]

    design_objs = []
    for i, d in enumerate(designs):
        d['technician'] = tech_objs[i % len(tech_objs)]
        design = NailDesign.objects.create(**d)
        design.auto_assign_style_tags()
        design_objs.append(design)

    print(f'  创建了 {len(design_objs)} 个款式')

    for cust in cust_objs:
        pref_data = {
            'customer': cust,
            'preferred_colors': random.choice(['粉色系,裸色系', '红色系,棕色系', '蓝色系,绿色系', '紫色系,黑色系']),
            'preferred_shapes': random.choice(['oval,squoval', 'almond,coffin', 'round,square', 'stiletto,coffin']),
            'preferred_styles': random.choice(['甜美,简约', '奢华,艺术', '清新,经典', '酷飒,新娘']),
            'preferred_occasions': random.choice(['日常,约会', '职场,派对', '婚礼,节日', '旅行,日常']),
        }
        CustomerPreference.objects.create(**pref_data)

    print(f'  创建了 {len(cust_objs)} 个顾客偏好')

    today = date.today()
    appointments = []
    for i in range(25):
        days_offset = random.randint(-60, 15)
        appt_date = today + timedelta(days=days_offset)
        hour = random.randint(10, 20)
        minute = random.choice([0, 30])
        from datetime import time
        appt_time = time(hour=hour, minute=minute)

        statuses = ['completed'] * 15 + ['confirmed'] * 4 + ['pending'] * 3 + ['in_progress'] * 2 + ['cancelled'] * 1
        status = statuses[min(i, len(statuses) - 1)]

        cust = random.choice(cust_objs)
        tech = random.choice(tech_objs)
        design = random.choice(design_objs) if random.random() > 0.2 else None

        appt = Appointment.objects.create(
            customer=cust,
            technician=tech,
            design=design,
            appointment_date=appt_date,
            appointment_time=appt_time,
            status=status,
            notes='顾客希望尽量保持自然' if random.random() > 0.5 else ''
        )
        appointments.append(appt)

    print(f'  创建了 {len(appointments)} 个预约')

    works_count = 0
    for appt in Appointment.objects.filter(status='completed'):
        works_count += 1
        completed_date = appt.appointment_date
        NailWork.objects.create(
            appointment=appt,
            customer=appt.customer,
            technician=appt.technician,
            design=appt.design,
            actual_nail_shape=appt.design.nail_shape if appt.design else 'oval',
            actual_color=appt.design.color_system if appt.design else '裸色系',
            duration_days=random.randint(10, 35),
            satisfaction=random.choice([4, 5, 5, 4, 5, 3, 5]),
            customer_feedback=random.choice([
                '非常满意，颜色很正！',
                '美甲师很专业，下次还来',
                '维持时间很久，不错',
                '款式很好看，朋友都问在哪做的',
                ''
            ]),
            completed_at=completed_date
        )

    print(f'  创建了 {works_count} 个作品存档')
    print('初始化数据完成！')


if __name__ == '__main__':
    run()
