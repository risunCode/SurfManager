// Matrix Rain Effect - Binary 0101 falling
(function () {
    const canvas = document.getElementById('matrix-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Set canvas size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Matrix characters - only binary
    const chars = '01';
    const fontSize = 14;
    const columns = canvas.width / fontSize;

    // Array for drops - one per column
    const drops = [];
    for (let i = 0; i < columns; i++) {
        drops[i] = Math.random() * -100; // Start at random heights
    }

    // Drawing function
    function draw() {
        // Semi-transparent black to create fade effect
        ctx.fillStyle = 'rgba(5, 8, 16, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Matrix green color
        ctx.fillStyle = '#00ff41';
        ctx.font = fontSize + 'px monospace';

        // Loop through drops
        for (let i = 0; i < drops.length; i++) {
            // Random character from chars
            const text = chars.charAt(Math.floor(Math.random() * chars.length));

            // Draw character
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);

            // Reset drop to top randomly after it crosses screen
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }

            // Increment Y coordinate
            drops[i]++;
        }
    }

    // Animation loop
    setInterval(draw, 35);

    // Resize handler
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
})();
