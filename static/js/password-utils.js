/**
 * Password Utilities for DailyHands
 * Handles password visibility toggle and live validation
 */

// Password validation rules (matching backend validation)
const PASSWORD_RULES = {
    minLength: 8,
    requireUppercase: true,
    requireLowercase: true,
    requireNumber: true,
    requireSpecial: true,
    specialChars: '!@#$%^&*(),.?":{}|<>'
};

/**
 * Initialize password visibility toggle for a password field
 * @param {string} passwordFieldId - ID of the password input field
 */
function initPasswordToggle(passwordFieldId) {
    const passwordField = document.getElementById(passwordFieldId);
    if (!passwordField) return;

    // Check if password field is inside a .form-floating container
    const formFloating = passwordField.closest('.form-floating');
    
    if (formFloating) {
        // For Bootstrap floating labels, add button directly to .form-floating
        // This preserves the input as direct child of .form-floating
        formFloating.style.position = 'relative';
        
        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'password-toggle-btn';
        toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
        toggleBtn.setAttribute('aria-label', 'Toggle password visibility');
        toggleBtn.style.cssText = `
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #64748b;
            cursor: pointer;
            padding: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.3s ease;
            z-index: 10;
        `;

        // Add hover effect
        toggleBtn.addEventListener('mouseenter', function() {
            this.style.color = '#6366f1';
        });
        toggleBtn.addEventListener('mouseleave', function() {
            this.style.color = '#64748b';
        });

        // Toggle password visibility
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const type = passwordField.getAttribute('type');
            if (type === 'password') {
                passwordField.setAttribute('type', 'text');
                this.innerHTML = '<i class="bi bi-eye-slash"></i>';
                this.setAttribute('aria-label', 'Hide password');
            } else {
                passwordField.setAttribute('type', 'password');
                this.innerHTML = '<i class="bi bi-eye"></i>';
                this.setAttribute('aria-label', 'Show password');
            }
        });

        // Adjust password field padding to make room for icon
        passwordField.style.paddingRight = '45px';

        // Insert toggle button into .form-floating (after input and label)
        formFloating.appendChild(toggleBtn);
        
    } else {
        // For non-floating labels, use wrapper approach (original behavior)
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        
        // Wrap the password field
        passwordField.parentNode.insertBefore(wrapper, passwordField);
        wrapper.appendChild(passwordField);

        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'password-toggle-btn';
        toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
        toggleBtn.setAttribute('aria-label', 'Toggle password visibility');
        toggleBtn.style.cssText = `
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #64748b;
            cursor: pointer;
            padding: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.3s ease;
            z-index: 10;
        `;

        // Add hover effect
        toggleBtn.addEventListener('mouseenter', function() {
            this.style.color = '#6366f1';
        });
        toggleBtn.addEventListener('mouseleave', function() {
            this.style.color = '#64748b';
        });

        // Toggle password visibility
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const type = passwordField.getAttribute('type');
            if (type === 'password') {
                passwordField.setAttribute('type', 'text');
                this.innerHTML = '<i class="bi bi-eye-slash"></i>';
                this.setAttribute('aria-label', 'Hide password');
            } else {
                passwordField.setAttribute('type', 'password');
                this.innerHTML = '<i class="bi bi-eye"></i>';
                this.setAttribute('aria-label', 'Show password');
            }
        });

        // Adjust password field padding to make room for icon
        passwordField.style.paddingRight = '45px';

        // Insert toggle button
        wrapper.appendChild(toggleBtn);
    }
}

/**
 * Validate password against all rules
 * @param {string} password - Password to validate
 * @returns {Object} - Validation result with isValid flag and errors array
 */
function validatePassword(password) {
    const errors = [];
    
    // Check minimum length
    if (password.length < PASSWORD_RULES.minLength) {
        errors.push({
            rule: 'length',
            message: `Minimum ${PASSWORD_RULES.minLength} characters`,
            valid: false
        });
    } else {
        errors.push({
            rule: 'length',
            message: `Minimum ${PASSWORD_RULES.minLength} characters`,
            valid: true
        });
    }

    // Check uppercase
    if (PASSWORD_RULES.requireUppercase) {
        const hasUppercase = /[A-Z]/.test(password);
        errors.push({
            rule: 'uppercase',
            message: 'At least 1 uppercase letter',
            valid: hasUppercase
        });
    }

    // Check lowercase
    if (PASSWORD_RULES.requireLowercase) {
        const hasLowercase = /[a-z]/.test(password);
        errors.push({
            rule: 'lowercase',
            message: 'At least 1 lowercase letter',
            valid: hasLowercase
        });
    }

    // Check number
    if (PASSWORD_RULES.requireNumber) {
        const hasNumber = /[0-9]/.test(password);
        errors.push({
            rule: 'number',
            message: 'At least 1 number',
            valid: hasNumber
        });
    }

    // Check special character
    if (PASSWORD_RULES.requireSpecial) {
        const specialCharsRegex = new RegExp(`[${PASSWORD_RULES.specialChars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}]`);
        const hasSpecial = specialCharsRegex.test(password);
        errors.push({
            rule: 'special',
            message: 'At least 1 special character (!@#$%^&*)',
            valid: hasSpecial
        });
    }

    const isValid = errors.every(e => e.valid);
    
    return {
        isValid: isValid,
        rules: errors
    };
}

/**
 * Initialize live password validation for a password field
 * @param {string} passwordFieldId - ID of the password input field
 * @param {string} feedbackContainerId - ID of the container to show validation feedback
 * @param {string} submitButtonId - Optional ID of submit button to enable/disable
 */
function initPasswordValidation(passwordFieldId, feedbackContainerId, submitButtonId = null) {
    const passwordField = document.getElementById(passwordFieldId);
    const feedbackContainer = document.getElementById(feedbackContainerId);
    const submitButton = submitButtonId ? document.getElementById(submitButtonId) : null;

    if (!passwordField || !feedbackContainer) return;

    // Create validation UI
    feedbackContainer.innerHTML = `
        <div class="password-validation-rules" style="margin-top: 0.5rem; font-size: 0.85rem;">
            <div class="validation-rule" data-rule="length">
                <i class="bi bi-circle"></i>
                <span>Minimum ${PASSWORD_RULES.minLength} characters</span>
            </div>
            <div class="validation-rule" data-rule="uppercase">
                <i class="bi bi-circle"></i>
                <span>At least 1 uppercase letter</span>
            </div>
            <div class="validation-rule" data-rule="lowercase">
                <i class="bi bi-circle"></i>
                <span>At least 1 lowercase letter</span>
            </div>
            <div class="validation-rule" data-rule="number">
                <i class="bi bi-circle"></i>
                <span>At least 1 number</span>
            </div>
            <div class="validation-rule" data-rule="special">
                <i class="bi bi-circle"></i>
                <span>At least 1 special character (!@#$%^&*)</span>
            </div>
        </div>
    `;

    // Add CSS for validation rules
    const style = document.createElement('style');
    style.textContent = `
        .password-validation-rules {
            padding: 0.75rem;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        .validation-rule {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.4rem;
            color: #64748b;
            transition: color 0.3s ease;
        }
        .validation-rule:last-child {
            margin-bottom: 0;
        }
        .validation-rule i {
            font-size: 0.75rem;
            transition: all 0.3s ease;
        }
        .validation-rule.valid {
            color: #10b981;
        }
        .validation-rule.valid i::before {
            content: "\\F26B"; /* bi-check-circle-fill */
        }
        .validation-rule.invalid {
            color: #ef4444;
        }
        .validation-rule.invalid i::before {
            content: "\\F659"; /* bi-x-circle-fill */
        }
    `;
    document.head.appendChild(style);

    // Validation function
    function updateValidation() {
        const password = passwordField.value;
        const result = validatePassword(password);

        // Update each rule's visual state
        result.rules.forEach(rule => {
            const ruleElement = feedbackContainer.querySelector(`[data-rule="${rule.rule}"]`);
            if (ruleElement) {
                ruleElement.classList.remove('valid', 'invalid');
                if (password.length > 0) {
                    ruleElement.classList.add(rule.valid ? 'valid' : 'invalid');
                }
            }
        });

        // Update password field border
        if (password.length > 0) {
            if (result.isValid) {
                passwordField.classList.remove('is-invalid');
                passwordField.classList.add('is-valid');
                // Add class to form-floating for icon spacing
                const formFloating = passwordField.closest('.form-floating');
                if (formFloating) {
                    formFloating.classList.add('has-validation-icon');
                }
            } else {
                passwordField.classList.remove('is-valid');
                passwordField.classList.add('is-invalid');
                // Add class to form-floating for icon spacing
                const formFloating = passwordField.closest('.form-floating');
                if (formFloating) {
                    formFloating.classList.add('has-validation-icon');
                }
            }
        } else {
            passwordField.classList.remove('is-valid', 'is-invalid');
            // Remove class from form-floating
            const formFloating = passwordField.closest('.form-floating');
            if (formFloating) {
                formFloating.classList.remove('has-validation-icon');
            }
        }

        // Enable/disable submit button
        if (submitButton) {
            if (password.length === 0 || result.isValid) {
                submitButton.disabled = false;
                submitButton.style.opacity = '1';
                submitButton.style.cursor = 'pointer';
            } else {
                submitButton.disabled = true;
                submitButton.style.opacity = '0.6';
                submitButton.style.cursor = 'not-allowed';
            }
        }

        return result.isValid;
    }

    // Add event listeners
    passwordField.addEventListener('input', updateValidation);
    passwordField.addEventListener('blur', updateValidation);

    // Initial validation if field has value
    if (passwordField.value) {
        updateValidation();
    }
}

/**
 * Initialize all password features for a form
 * @param {Object} config - Configuration object
 * @param {string} config.passwordFieldId - ID of password field
 * @param {string} config.feedbackContainerId - ID of feedback container (for validation)
 * @param {string} config.submitButtonId - ID of submit button (optional)
 * @param {boolean} config.enableToggle - Enable visibility toggle (default: true)
 * @param {boolean} config.enableValidation - Enable live validation (default: false)
 */
function initPasswordFeatures(config) {
    const {
        passwordFieldId,
        feedbackContainerId = null,
        submitButtonId = null,
        enableToggle = true,
        enableValidation = false
    } = config;

    // Initialize password visibility toggle
    if (enableToggle) {
        initPasswordToggle(passwordFieldId);
    }

    // Initialize live password validation
    if (enableValidation && feedbackContainerId) {
        initPasswordValidation(passwordFieldId, feedbackContainerId, submitButtonId);
    }
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initPasswordToggle,
        initPasswordValidation,
        initPasswordFeatures,
        validatePassword
    };
}
