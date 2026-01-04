// Contact Form
const contactForm = document.getElementById('contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitButton = this.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;
        
        // Отключаем кнопку и показываем загрузку
        submitButton.disabled = true;
        submitButton.textContent = 'Отправка...';
        
        try {
            const formData = new FormData(this);
            
            const response = await fetch('/submit-contact/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(data.message);
                this.reset();
            } else {
                alert(data.error || 'Произошла ошибка при отправке заявки');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при отправке заявки. Попробуйте позже.');
        } finally {
            // Возвращаем кнопку в исходное состояние
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    });
}