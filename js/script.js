// Hint Button Functionality
document.addEventListener('DOMContentLoaded', function() {
    const hintButton = document.querySelector('.hint-button');
    const hints = [
        "Look closely at the patterns...",
        "Some things are hidden in plain sight...",
        "The key might not be where you expect it..."
    ];
    let hintIndex = 0;

    if (hintButton) {
        hintButton.addEventListener('click', function() {
            this.textContent = hints[hintIndex];
            hintIndex = (hintIndex + 1) % hints.length;
        });
    }

    // Smooth Scrolling for Navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add glitch effect to the hero section text
    const heroTitle = document.querySelector('.hero h1');
    if (heroTitle) {
        setInterval(() => {
            heroTitle.style.textShadow = `
                ${Math.random() * 10}px ${Math.random() * 10}px ${Math.random() * 30}px rgba(0, 242, 255, 0.5)
            `;
        }, 100);
    }
});