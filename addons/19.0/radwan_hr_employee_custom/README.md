# radwan_hr_employee_custom

موديول مخصص لـ Odoo 19 Community لإضافة حقول موارد بشرية مخصصة على ملف الموظف.

## طريقة الاستخدام

1. انسخ مجلد `radwan_hr_employee_custom` إلى:
   `C:\Program Files\Odoo 19.0.20260516\custom_addons`

2. تأكد من وجود المسار التالي داخل `addons_path`:
   `C:\Program Files\Odoo 19.0.20260516\custom_addons`

3. ثبّت مكتبة التحويل الهجري:
   `"C:\Program Files\Odoo 19.0.20260516\python\python.exe" -m pip install hijridate`

4. أعد تشغيل خدمة Odoo من Services.

5. من Odoo:
   Apps > Update Apps List > ابحث عن Radwan HR Employee Custom Fields > Activate/Upgrade


## Scheduled Action

تمت إضافة Scheduled Action باسم:
`Radwan HR Employee: Refresh Expiry Statuses`

وظيفتها تحديث حالات الانتهاء يوميًا حتى تظل الفلاتر والتجميعات ووسوم القائمة صحيحة مع مرور الأيام.


## Final Expiry Monitoring Fix

تم نقل شاشة المتابعة إلى:
Employees > Reporting > Expiry Monitoring

سبب التصحيح:
- تم حذف الاعتماد على parent خارجي غير موجود في Odoo 19.
- تم استخدام parent الصحيح في Odoo 19 HR: hr.hr_menu_hr_reports
- تم تعطيل محاولات القوائم القديمة حتى لا توجه إلى Action خاطئ.


## HR Employee PDF Reports

تمت إضافة 10 تقارير PDF احترافية تظهر من قائمة Print داخل ملف الموظف:

1. HR Reports | 01 Employee Profile Card
2. HR Reports | 02 Work & Organization Summary
3. HR Reports | 03 Personal & Identity Summary
4. HR Reports | 04 ID / Iqama Compliance Report
5. HR Reports | 05 Passport & Travel Documents
6. HR Reports | 06 Medical Insurance Report
7. HR Reports | 07 Contract & Employment Terms
8. HR Reports | 08 Expiry Status Matrix
9. HR Reports | 09 Contact & Emergency Report
10. HR Reports | 10 Complete Employee File
