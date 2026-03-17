// Main JavaScript file for E-Banking System

// Form validation and real-time checking
document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Mobile number validation
    const mobileInputs = document.querySelectorAll('input[type="tel"], input[name="mobile"]');
    mobileInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 10) {
                this.value = this.value.slice(0, 10);
            }
            validateMobile(this);
        });
    });

    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"], input[name="email"]');
    emailInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            validateEmail(this);
        });
    });

    // Amount validation
    const amountInputs = document.querySelectorAll('input[name="amount"]');
    amountInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            validateAmount(this);
        });
    });

    // Confirmation dialogs for sensitive actions
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to close this account? This action cannot be undone!')) {
                e.preventDefault();
            }
        });
    });

    const transferForms = document.querySelectorAll('.transfer-form');
    transferForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const amount = document.querySelector('input[name="amount"]').value;
            const toAccount = document.querySelector('input[name="to_account"]').value;
            
            if (!confirm(`Are you sure you want to transfer ₹${parseFloat(amount).toFixed(2)} to account ${toAccount}?`)) {
                e.preventDefault();
            }
        });
    });
});

// Validation Functions
function validateMobile(input) {
    const mobile = input.value;
    const statusDiv = document.getElementById('mobile-status');
    
    if (mobile.length === 10) {
        if (statusDiv) {
            statusDiv.className = 'verification-status verification-success';
            statusDiv.textContent = '✓ Valid mobile number';
        }
        
        // Check if mobile exists (if we're on create account page)
        if (window.location.pathname.includes('create-account')) {
            checkMobileExists(mobile);
        }
    } else {
        if (statusDiv) {
            statusDiv.className = 'verification-status verification-error';
            statusDiv.textContent = '✗ Mobile number must be 10 digits';
        }
    }
}

function validateEmail(input) {
    const email = input.value;
    const statusDiv = document.getElementById('email-status');
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    
    if (emailPattern.test(email)) {
        if (statusDiv) {
            statusDiv.className = 'verification-status verification-success';
            statusDiv.textContent = '✓ Valid email format';
        }
        
        // Check if email exists (if we're on create account page)
        if (window.location.pathname.includes('create-account')) {
            checkEmailExists(email);
        }
    } else {
        if (statusDiv) {
            statusDiv.className = 'verification-status verification-error';
            statusDiv.textContent = '✗ Invalid email format';
        }
    }
}

function validateAmount(input) {
    const amount = parseFloat(input.value);
    const statusDiv = document.getElementById('amount-status');
    
    if (amount > 0) {
        if (statusDiv) {
            statusDiv.className = 'verification-status verification-success';
            statusDiv.textContent = `✓ Amount: ₹${amount.toFixed(2)}`;
        }
    } else {
        if (statusDiv) {
            statusDiv.className = 'verification-status verification-error';
            statusDiv.textContent = '✗ Amount must be greater than 0';
        }
    }
}

// AJAX functions to check existence
function checkMobileExists(mobile) {
    fetch('/check-mobile', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({mobile: mobile})
    })
    .then(response => response.json())
    .then(data => {
        const statusDiv = document.getElementById('mobile-status');
        if (data.exists) {
            statusDiv.className = 'verification-status verification-error';
            statusDiv.textContent = '✗ This mobile number is already registered';
        }
    })
    .catch(error => console.error('Error:', error));
}

function checkEmailExists(email) {
    fetch('/check-email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({email: email})
    })
    .then(response => response.json())
    .then(data => {
        const statusDiv = document.getElementById('email-status');
        if (data.exists) {
            statusDiv.className = 'verification-status verification-error';
            statusDiv.textContent = '✗ This email is already registered';
        }
    })
    .catch(error => console.error('Error:', error));
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

// Show loading spinner
function showLoading() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    spinner.id = 'loading-spinner';
    document.body.appendChild(spinner);
}

// Hide loading spinner
function hideLoading() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.remove();
    }
}

// Copy to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        alert('Account number copied to clipboard!');
    }, function(err) {
        console.error('Could not copy text: ', err);
    });
}

// Print function for statements
function printStatement() {
    window.print();
}

// Real-time balance check for withdrawals
function checkWithdrawalBalance() {
    const amountInput = document.querySelector('input[name="amount"]');
    const currentBalance = parseFloat(document.getElementById('current-balance')?.value || 0);
    const warningDiv = document.getElementById('withdrawal-warning');
    
    if (amountInput) {
        amountInput.addEventListener('input', function() {
            const withdrawalAmount = parseFloat(this.value) || 0;
            
            if (warningDiv) {
                if (withdrawalAmount > currentBalance) {
                    warningDiv.style.display = 'block';
                    warningDiv.textContent = '⚠️ Insufficient balance!';
                    warningDiv.className = 'verification-status verification-error';
                } else {
                    warningDiv.style.display = 'none';
                }
            }
        });
    }
}

// Initialize page-specific functions
function initPage() {
    if (window.location.pathname.includes('withdraw')) {
        checkWithdrawalBalance();
    }
}

// Call init when DOM is loaded
document.addEventListener('DOMContentLoaded', initPage);