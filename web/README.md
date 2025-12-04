# SurfManager Website

> Modern landing page and documentation for SurfManager - Advanced Session & Data Management Tool
 
```

## 🎨 Features

### Landing Page (`index.html`)
- **Hero Section** - Terminal-style introduction with animated cursor
- **Features Grid** - 6 key features showcase
- **About Section** - Detailed information and use cases
- **Gallery** - 2x2 grid layout for screenshots
- **Footer** - Links and platform information
- **Matrix Background** - Animated Matrix-style background effect

### Documentation Page (`docs.html`)
- **Live README Loading** - Fetches from GitHub repository
- **Sidebar TOC** - Fixed sidebar with table of contents
- **Scroll Spy** - Auto-highlight current section
- **Markdown Rendering** - Client-side markdown to HTML conversion
- **No Footer** - Clean, focused documentation view

## 🛠️ Technology Stack

- **CSS Framework**: Tailwind CSS (CDN)
- **JavaScript**: Vanilla JS (no frameworks)
- **Icons**: Unicode & Emoji
- **Background**: Custom Canvas animation
- **Meta Tags**: Open Graph & Twitter Cards

## 🎯 Design Theme

**Terminal/Hacker Aesthetic:**
- Dark background (`#0a0e27`)
- Matrix green (`#00ff41`)
- Cyan highlights (`#00d4ff`)
- Monospace fonts
- Scan-line effects
- Terminal-style text

## 🚀 Usage

### Local Development
1. Simply open `index.html` or `docs.html` in a browser
2. No build process required
3. All dependencies loaded via CDN

### Deployment
- Static site (no backend required)
- Can be hosted on:
  - GitHub Pages
  - Netlify
  - Vercel
  - Any static hosting

## 📝 Content Guidelines

### Brand Censoring
Brand names are partially censored with `**`:
- Cur**r (instead of full name)
- Wind**rf (instead of full name)
- Visual Studio Code (allowed in full)
- VSCode (allowed in full)

### Meta Information
All meta tags include:
- SEO-optimized descriptions
- Open Graph tags for social sharing
- Twitter Card tags
- Schema.org structured data

## 🔧 Customization

### Colors
Edit Tailwind config in `<script>` tag:
```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                terminal: {
                    bg: '#0a0e27',
                    dark: '#050810',
                    border: '#1a1f3a',
                    green: '#00ff41',
                    cyan: '#00d4ff',
                    gray: '#8b949e',
                }
            }
        }
    }
}
```

### Matrix Effect
Modify `assets/js/matrix.js` for background customization.

## 📱 Responsive Design

- **Desktop**: Full layout with sidebar (1280px+)
- **Tablet**: Collapsed sidebar, responsive grid
- **Mobile**: Hamburger menu, single column layout

## 🔗 Links

- **GitHub**: https://github.com/risunCode/SurfManager
- **Releases**: https://github.com/risunCode/SurfManager/releases
- **Issues**: https://github.com/risunCode/SurfManager/issues

## 📦 Backups

Backup files are created with `.backup2` extension:
- `index.html.backup2`
- `docs.html.backup2`

To restore: `Copy-Item index.html.backup2 index.html -Force`

## 🎨 Assets

### Images Required
- `assets/images/v1.jpg` - Main interface screenshot
- `assets/images/v2.jpg` - Account manager screenshot
- `assets/images/v3.jpg` - Settings screenshot
- `assets/images/v4.jpg` - System info screenshot

### Scripts
- `assets/js/matrix.js` - Matrix rain effect
- `assets/js/enhanced.js` - Additional features

## ⚡ Performance

- **Startup**: Instant (static files)
- **Matrix Effect**: Optimized canvas rendering
- **Tailwind CSS**: JIT compilation via CDN
- **Images**: Lazy loading ready

## 🐛 Known Issues

None currently. See GitHub Issues for bug reports.

## 📄 License

MIT License - Same as main project

---

**Version**: 5.1.2  
**Author**: risunCode  
**Last Updated**: November 2025
