        // Slide-out Menu
        const burgerBtn = document.getElementById('burger-btn');
        const slideMenu = document.getElementById('slide-menu');
        const menuOverlay = document.getElementById('menu-overlay');
        const closeMenuBtn = document.getElementById('close-menu-btn');
        const menuIcon = document.getElementById('menu-icon');
        const closeIcon = document.getElementById('close-icon');

        function openMenu() {
            slideMenu.classList.remove('translate-x-full');
            menuOverlay.classList.remove('opacity-0', 'invisible');
            menuIcon.classList.add('hidden');
            closeIcon.classList.remove('hidden');
            document.body.style.overflow = 'hidden'; // Prevent scrolling
        }

        function closeMenu() {
            slideMenu.classList.add('translate-x-full');
            menuOverlay.classList.add('opacity-0', 'invisible');
            menuIcon.classList.remove('hidden');
            closeIcon.classList.add('hidden');
            document.body.style.overflow = ''; // Restore scrolling
        }

        burgerBtn.addEventListener('click', openMenu);
        closeMenuBtn.addEventListener('click', closeMenu);
        menuOverlay.addEventListener('click', closeMenu);

        // Close menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeMenu();
            }
        });

        // Smooth scrolling
        function scrollToSection(sectionId) {
            const element = document.getElementById(sectionId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
                closeMenu(); // Close slide-out menu
            }
        }

        // Photo Carousel
        const photos = [
            {
                src: '/professional-woman-working-on-social-media-content.png',
                alt: 'Работа над SMM контентом'
            },
            {
                src: '/ai-content-creation-workspace-with-laptop-and-grap.png',
                alt: 'Создание AI контента'
            },
            {
                src: '/social-media-analytics-dashboard-on-computer-scree.png',
                alt: 'Аналитика социальных сетей'
            },
            {
                src: '/creative-content-planning-and-strategy-session.png',
                alt: 'Планирование контент-стратегии'
            }
        ];

        let currentPhotoIndex = 0;
        const carouselImage = document.getElementById('carousel-image');
        const carouselDots = document.getElementById('carousel-dots').children;

        function updateCarousel() {
            carouselImage.src = photos[currentPhotoIndex].src;
            carouselImage.alt = photos[currentPhotoIndex].alt;
            
            // Update dots
            for (let i = 0; i < carouselDots.length; i++) {
                if (i === currentPhotoIndex) {
                    carouselDots[i].classList.remove('bg-light-gray');
                    carouselDots[i].classList.add('bg-navy');
                } else {
                    carouselDots[i].classList.remove('bg-navy');
                    carouselDots[i].classList.add('bg-light-gray');
                }
            }
        }

        function nextPhoto() {
            currentPhotoIndex = (currentPhotoIndex + 1) % photos.length;
            updateCarousel();
        }

        function previousPhoto() {
            currentPhotoIndex = (currentPhotoIndex - 1 + photos.length) % photos.length;
            updateCarousel();
        }

        function goToPhoto(index) {
            currentPhotoIndex = index;
            updateCarousel();
        }

        // Auto-advance carousel
        setInterval(nextPhoto, 5000);

        // Contact Form
        document.getElementById('contact-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            console.log('Form submitted:', data);
            alert('Спасибо за заявку! Я свяжусь с вами в ближайшее время.');
            
            // Reset form
            this.reset();
        });

        // FAQ toggle functionality
        function toggleFAQ(button) {
            const faqItem = button.parentElement;
            const answer = faqItem.querySelector('.faq-answer');
            const icon = button.querySelector('.faq-icon');
            
            if (answer.style.maxHeight && answer.style.maxHeight !== '0px') {
                // Close
                answer.style.maxHeight = '0px';
                answer.style.opacity = '0';
                icon.textContent = '+';
                icon.style.transform = 'rotate(0deg)';
            } else {
                // Open
                answer.style.maxHeight = answer.scrollHeight + 'px';
                answer.style.opacity = '1';
                icon.textContent = '−';
                icon.style.transform = 'rotate(180deg)';
            }
        }

        // Function for "All Cases" button (placeholder for future implementation)
        function showAllCases() {
            // This could be expanded to load more cases dynamically or navigate to a dedicated page
            alert('Просмотр всех кейсов. Функциональность в разработке.');
        }
