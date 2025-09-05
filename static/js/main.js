// DOM elements
const shortenForm = document.getElementById('shorten-form');
const urlInput = document.getElementById('url');
const customCodeInput = document.getElementById('custom_code');
const resultContainer = document.getElementById('result');
const shortenedUrlInput = document.getElementById('shortened-url');
const copyBtn = document.getElementById('copy-btn');
const previewContent = document.getElementById('preview-content');
const qrCodeImg = document.getElementById('qr-code');
const errorMessage = document.getElementById('error-message');
const shareButtons = document.querySelectorAll('.share-btn');

// Form submission handler
shortenForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const url = urlInput.value.trim();
    const customCode = customCodeInput.value.trim();
    
    if (!url) {
        showError('Please enter a URL');
        return;
    }
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('url', url);
        if (customCode) {
            formData.append('custom_code', customCode);
        }
        
        // Send request to shorten URL
        const response = await fetch('/shorten', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Display result
            displayResult(data.short_url, data.short_code);
            
            // Hide error message if visible
            hideError();
        } else {
            showError(data.error || 'Failed to shorten URL');
        }
    } catch (error) {
        showError('Network error. Please try again.');
        console.error('Error shortening URL:', error);
    }
});

// Display shortened URL result
function displayResult(shortUrl, shortCode) {
    shortenedUrlInput.value = shortUrl;
    resultContainer.style.display = 'block';
    
    // Load preview
    loadPreview(shortCode);
    
    // Load QR code
    loadQRCode(shortCode);
}

// Copy shortened URL to clipboard
copyBtn.addEventListener('click', function() {
    shortenedUrlInput.select();
    document.execCommand('copy');
    
    // Change button text temporarily
    const originalText = copyBtn.textContent;
    copyBtn.textContent = 'Copied!';
    setTimeout(() => {
        copyBtn.textContent = originalText;
    }, 2000);
});

// Load preview of original URL
async function loadPreview(shortCode) {
    try {
        const response = await fetch(`/preview/${shortCode}`);
        const data = await response.json();
        
        if (response.ok) {
            previewContent.textContent = data.original_url;
        } else {
            previewContent.textContent = 'Preview not available';
        }
    } catch (error) {
        previewContent.textContent = 'Preview not available';
        console.error('Error loading preview:', error);
    }
}

// Load QR code for shortened URL
async function loadQRCode(shortCode) {
    try {
        const response = await fetch(`/qr/${shortCode}`);
        const data = await response.json();
        
        if (response.ok) {
            qrCodeImg.src = `data:image/png;base64,${data.qr_code}`;
        } else {
            qrCodeImg.alt = 'QR code not available';
        }
    } catch (error) {
        qrCodeImg.alt = 'QR code not available';
        console.error('Error loading QR code:', error);
    }
}

// Social media sharing
shareButtons.forEach(button => {
    button.addEventListener('click', function() {
        const platform = this.getAttribute('data-platform');
        const url = shortenedUrlInput.value;
        
        shareToPlatform(platform, url);
    });
});

// Share to specific platform
function shareToPlatform(platform, url) {
    let shareUrl;
    
    switch (platform) {
        case 'twitter':
            shareUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=Check out this link!`;
            break;
        case 'facebook':
            shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
            break;
        case 'linkedin':
            shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
            break;
        case 'email':
            shareUrl = `mailto:?subject=Check out this link&body=${encodeURIComponent(url)}`;
            break;
        default:
            shareUrl = url;
    }
    
    window.open(shareUrl, '_blank');
}

// Show error message
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    
    // Hide result container if visible
    resultContainer.style.display = 'none';
}

// Hide error message
function hideError() {
    errorMessage.style.display = 'none';
}

// Simple form validation
urlInput.addEventListener('input', function() {
    if (this.value.trim()) {
        hideError();
    }
});