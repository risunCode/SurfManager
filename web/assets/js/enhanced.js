/**
 * SurfManager Website - Enhanced JavaScript
 * Additional interactive features and effects
 */

// Enhanced terminal typing effect
class TerminalTyper {
    constructor(element, text, speed = 50) {
        this.element = element;
        this.text = text;
        this.speed = speed;
        this.index = 0;
    }
    
    type() {
        if (this.index < this.text.length) {
            this.element.textContent += this.text.charAt(this.index);
            this.index++;
            setTimeout(() => this.type(), this.speed);
        }
    }
    
    start() {
        this.element.textContent = '';
        this.type();
    }
}

// Matrix rain effect (optional background)
class MatrixRain {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        this.chars = "01";
        this.fontSize = 14;
        this.columns = this.canvas.width / this.fontSize;
        this.drops = [];
        
        for (let i = 0; i < this.columns; i++) {
            this.drops[i] = Math.random() * -100;
        }
    }
    
    draw() {
        if (!this.ctx) return;
        
        this.ctx.fillStyle = 'rgba(5, 8, 16, 0.05)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.ctx.fillStyle = '#00ff41';
        this.ctx.font = this.fontSize + 'px monospace';
        
        for (let i = 0; i < this.drops.length; i++) {
            const text = this.chars.charAt(Math.floor(Math.random() * this.chars.length));
            this.ctx.fillText(text, i * this.fontSize, this.drops[i] * this.fontSize);
            
            if (this.drops[i] * this.fontSize > this.canvas.height && Math.random() > 0.975) {
                this.drops[i] = 0;
            }
            this.drops[i]++;
        }
    }
    
    start() {
        setInterval(() => this.draw(), 35);
    }
}

// Smooth parallax scroll effect
function initParallax() {
    const parallaxElements = document.querySelectorAll('.parallax');
    
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        
        parallaxElements.forEach(element => {
            const speed = element.dataset.speed || 0.5;
            element.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });
}

// Easter egg: Konami code
function initKonamiCode() {
    const konamiCode = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65];
    let konamiIndex = 0;
    
    document.addEventListener('keydown', (e) => {
        if (e.keyCode === konamiCode[konamiIndex]) {
            konamiIndex++;
            if (konamiIndex === konamiCode.length) {
                activateEasterEgg();
                konamiIndex = 0;
            }
        } else {
            konamiIndex = 0;
        }
    });
}

function activateEasterEgg() {
    // Add special effect when konami code is entered
    document.body.style.animation = 'rainbow 2s linear infinite';
    setTimeout(() => {
        document.body.style.animation = '';
    }, 5000);
    
    console.log('%c🎮 KONAMI CODE ACTIVATED! 🎮', 'color: #00ff41; font-size: 20px; font-weight: bold;');
}

// Analytics helper (placeholder)
function trackEvent(category, action, label) {
    console.log(`Analytics: ${category} - ${action} - ${label}`);
    // Add your analytics code here (Google Analytics, etc.)
}

// Copy to clipboard helper
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Notification toast
function showNotification(message, duration = 3000) {
    const notification = document.createElement('div');
    notification.className = 'fixed bottom-4 right-4 bg-terminal-green text-terminal-dark px-6 py-3 font-bold z-50 glow-border';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.5s';
        setTimeout(() => notification.remove(), 500);
    }, duration);
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    // Track page view
    trackEvent('Page', 'View', 'Home');
    
    // Initialize parallax if elements exist
    if (document.querySelector('.parallax')) {
        initParallax();
    }
    
    // Initialize konami code easter egg
    initKonamiCode();
    
    // Track download button clicks
    document.querySelectorAll('a[href*="download"], a[href*="releases"]').forEach(link => {
        link.addEventListener('click', () => {
            trackEvent('Download', 'Click', link.href);
        });
    });
    
    // Add copy code functionality
    document.querySelectorAll('pre code').forEach(block => {
        const button = document.createElement('button');
        button.className = 'absolute top-2 right-2 bg-terminal-green text-terminal-dark px-2 py-1 text-xs';
        button.textContent = 'COPY';
        button.onclick = () => {
            copyToClipboard(block.textContent);
        };
        
        if (block.parentElement.style.position !== 'relative') {
            block.parentElement.style.position = 'relative';
        }
        block.parentElement.appendChild(button);
    });
});

// Export for use in other scripts
window.SurfManager = {
    TerminalTyper,
    MatrixRain,
    trackEvent,
    copyToClipboard,
    showNotification
};
