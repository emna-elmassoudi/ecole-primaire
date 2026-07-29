document.addEventListener('DOMContentLoaded', function () {

    /* ====== NAVBAR TOGGLE ====== */
    var navToggle = document.getElementById('navToggle');
    var navMenu = document.getElementById('navMenu');
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function () {
            navMenu.classList.toggle('active');
            document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
        });
        document.addEventListener('click', function (e) {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }

    /* ====== NAVBAR SCROLL SHADOW ====== */
    var navbarWrapper = document.getElementById('navbarWrapper');
    if (navbarWrapper) {
        window.addEventListener('scroll', function () {
            navbarWrapper.classList.toggle('scrolled', window.scrollY > 20);
        });
    }

    /* ====== ADMIN SIDEBAR ====== */
    var sidebarToggle = document.getElementById('sidebarToggle');
    var sidebarClose = document.getElementById('sidebarClose');
    var adminSidebar = document.getElementById('adminSidebar');
    if (sidebarToggle && adminSidebar) {
        sidebarToggle.addEventListener('click', function () { adminSidebar.classList.toggle('active'); });
    }
    if (sidebarClose && adminSidebar) {
        sidebarClose.addEventListener('click', function () { adminSidebar.classList.remove('active'); });
    }

    /* ====== FLASH MESSAGES ====== */
    document.querySelectorAll('.flash-message').forEach(function (msg) {
        setTimeout(function () {
            if (msg.parentElement) {
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-10px)';
                msg.style.transition = 'all 0.3s ease';
                setTimeout(function () { if (msg.parentElement) msg.remove(); }, 300);
            }
        }, 5000);
    });

    /* ====== LIGHTBOX ====== */
    var lightbox = document.getElementById('lightbox');
    if (lightbox) {
        window.openLightbox = function (src, caption) {
            var img = document.getElementById('lightboxImage');
            var cap = document.getElementById('lightboxCaption');
            if (img) img.src = src;
            if (cap) cap.textContent = caption || '';
            lightbox.classList.add('active');
            document.body.style.overflow = 'hidden';
        };
        window.closeLightbox = function () {
            lightbox.classList.remove('active');
            document.body.style.overflow = '';
        };
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && lightbox.classList.contains('active')) {
                window.closeLightbox();
            }
        });
    }

    /* ====== FAQ TOGGLE ====== */
    window.toggleFaq = function (el) {
        var item = el.parentElement;
        item.classList.toggle('active');
    };

    /* ====== SCROLL REVEAL ====== */
    if ('IntersectionObserver' in window) {
        var revealObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

        document.querySelectorAll('.reveal').forEach(function (el) {
            revealObserver.observe(el);
        });
    } else {
        document.querySelectorAll('.reveal').forEach(function (el) {
            el.classList.add('visible');
        });
    }

    /* ====== COUNTER ANIMATION ====== */
    var countersAnimated = false;

    function animateCounters() {
        if (countersAnimated) return;
        document.querySelectorAll('.stat-number[data-target]').forEach(function (counter) {
            var target = parseInt(counter.getAttribute('data-target'));
            var current = 0;
            var increment = Math.ceil(target / 60);
            var timer = setInterval(function () {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                // Handle percentage with small tag
                var text = counter.innerHTML;
                if (text.includes('<small')) {
                    counter.innerHTML = current + '<small style="font-size:1.5rem;">%</small>';
                } else {
                    counter.textContent = current;
                }
            }, 25);
        });
        countersAnimated = true;
    }

    if ('IntersectionObserver' in window) {
        var statsSection = document.querySelector('.stats-section');
        if (statsSection) {
            var statsObserver = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        animateCounters();
                        statsObserver.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.3 });
            statsObserver.observe(statsSection);
        }
    }

    /* ====== AUTO-SUBMIT PHOTO UPLOAD ====== */
    var photoInput = document.getElementById('photoUploadInput');
    if (photoInput) {
        photoInput.addEventListener('change', function () {
            if (this.files && this.files.length > 0) {
                document.getElementById('photoUploadForm').submit();
            }
        });
    }

    /* ====== NOTIFICATION DROPDOWN ====== */
    var notifToggle = document.getElementById('notifToggle');
    var notifDropdown = document.getElementById('notifDropdown');
    if (notifToggle && notifDropdown) {
        var badge = notifToggle.querySelector('.badge');
        if (badge && parseInt(badge.textContent) > 0) {
            badge.classList.add('pulse');
        }
        notifToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            notifDropdown.classList.toggle('active');
        });
        document.addEventListener('click', function (e) {
            if (!notifToggle.contains(e.target) && !notifDropdown.contains(e.target)) {
                notifDropdown.classList.remove('active');
            }
        });
    }

    /* ====== SMOOTH SCROLL FOR ANCHOR LINKS ====== */
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

});
