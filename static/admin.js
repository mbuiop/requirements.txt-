// اسکریپت مدیریت برای دکمه‌های ادمین
document.addEventListener('DOMContentLoaded', function() {
    // اضافه کردن رویداد کلیک برای دکمه‌های ادمین
    const adminButtons = document.querySelectorAll('.admin-btn');
    adminButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('آیا می‌خواهید به پنل مدیریت وارد شوید؟')) {
                e.preventDefault();
            }
        });
    });
    
    // مدیریت فرم‌ها
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'در حال پردازش...';
            }
        });
    });
});
