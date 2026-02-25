document.addEventListener('DOMContentLoaded', () => {
    // Toggle password visibility
    function togglePassword(id) {
        const input = document.getElementById(id);
        const icon = input?.nextElementSibling;
        if (input && icon) {
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        }
    }

    // Show Security Question Popup
    function showSecurityQuestionPopup(question, userId) {
        let popup = document.createElement('div');
        popup.className = 'security-popup';
        popup.innerHTML = `
            <div class="popup-content">
                <i class="fas fa-question-circle"></i>
                <p>${question}</p>
                <div class="input-group">
                    <input type="text" id="popup-security-answer" placeholder="Enter Answer" required>
                </div>
                <button class="close-popup">Submit</button>
            </div>
        `;
        document.body.appendChild(popup);

        document.querySelector('.close-popup')?.addEventListener('click', () => {
            const securityAnswer = document.getElementById('popup-security-answer')?.value;
            if (securityAnswer) {
                handleSecurityAnswer(userId, securityAnswer);
            }
            document.body.removeChild(popup);
        });

        setTimeout(() => {
            if (document.body.contains(popup)) {
                document.body.removeChild(popup);
            }
        }, 30000);
    }

    // Handle Security Answer
    async function handleSecurityAnswer(userId, securityAnswer) {
        const formData = new FormData();
        formData.append('user_id', userId);
        formData.append('security_answer', securityAnswer);
        formData.append('step', 'security_question');

        try {
            const response = await fetch('/forgot-password', { method: 'POST', body: formData });
            const result = await response.json();
            const output = document.getElementById('forgot-output');
            if (output) {
                if (result.status === 'success' && result.step === 'reset_password') {
                    window.location.href = `/reset-password?user_id=${result.user_id}`;
                } else {
                    output.textContent = result.message || 'Unknown error';
                }
            }
        } catch (error) {
            const output = document.getElementById('forgot-output');
            if (output) output.textContent = 'Network error: ' + error.message;
            console.error('Security answer error:', error);
        }
    }

    // Login Handler
    document.getElementById('login-btn')?.addEventListener('click', async () => {
        const userId = document.getElementById('login-user-id')?.value;
        const password = document.getElementById('login-password')?.value;
        const output = document.getElementById('login-output');
        if (output) {
            if (!userId || !password) {
                output.textContent = 'Please enter both User ID and Password';
                return;
            }
            const formData = new FormData();
            formData.append('user_id', userId);
            formData.append('password', password);

            try {
                const response = await fetch('/login', { method: 'POST', body: formData });
                const result = await response.json();
                if (result.status === 'success') {
                    window.location.href = result.redirect;
                } else {
                    output.textContent = result.message || 'Login failed';
                }
            } catch (error) {
                output.textContent = 'Network error';
                console.error('Login error:', error);
            }
        }
    });

    // Signup Handler
    document.getElementById('submit-signup-btn')?.addEventListener('click', async () => {
        const userId = document.getElementById('signup-user-id')?.value;
        const password = document.getElementById('signup-password')?.value;
        const securityQuestion = document.getElementById('security-question')?.value;
        const securityAnswer = document.getElementById('security-answer')?.value;
        const output = document.getElementById('signup-output');
        if (output) {
            if (!userId || !password || !securityQuestion || !securityAnswer) {
                output.textContent = 'All fields are required';
                return;
            }
            const formData = new FormData();
            formData.append('user_id', userId);
            formData.append('password', password);
            formData.append('security_question', securityQuestion);
            formData.append('security_answer', securityAnswer);

            try {
                const response = await fetch('/signup', { method: 'POST', body: formData });
                const result = await response.json();
                if (result.status === 'success') {
                    window.location.href = result.redirect || '/login-page';
                } else {
                    output.textContent = result.message || 'Signup failed';
                }
            } catch (error) {
                output.textContent = 'Network error: ' + error.message;
                console.error('Signup error:', error);
            }
        }
    });

    // Forgot Password Handler
    document.getElementById('forgot-password-btn')?.addEventListener('click', async () => {
        const step = document.getElementById('forgot-step')?.value || 'user_id';
        const formData = new FormData();
        const output = document.getElementById('forgot-output');

        if (output && step === 'user_id') {
            const userId = document.getElementById('forgot-user-id')?.value;
            if (!userId) {
                output.textContent = 'Please enter User ID';
                return;
            }
            formData.append('user_id', userId);
            formData.append('step', 'user_id');

            try {
                const response = await fetch('/forgot-password', { method: 'POST', body: formData });
                const result = await response.json();
                if (result.status === 'success' && result.step === 'security_question') {
                    showSecurityQuestionPopup(result.security_question, result.user_id);
                } else {
                    output.textContent = result.message || 'Unknown error';
                }
            } catch (error) {
                output.textContent = 'Network error: ' + error.message;
                console.error('Forgot password error:', error);
            }
        }
    });

    // Reset Password Handler
    document.getElementById('reset-password-btn')?.addEventListener('click', async () => {
        const userId = document.getElementById('reset-user-id')?.value;
        const newPassword = document.getElementById('reset-new-password')?.value;
        const confirmPassword = document.getElementById('reset-confirm-password')?.value;
        const output = document.getElementById('reset-output');

        if (output) {
            if (!newPassword || !confirmPassword) {
                output.textContent = 'Please fill in both password fields';
                return;
            }
            if (newPassword !== confirmPassword) {
                output.textContent = 'Passwords do not match';
                return;
            }

            const formData = new FormData();
            formData.append('user_id', userId);
            formData.append('new_password', newPassword);
            formData.append('confirm_password', confirmPassword);
            formData.append('step', 'reset_password');

            try {
                const response = await fetch('/reset-password', { method: 'POST', body: formData });
                const result = await response.json();
                if (result.status === 'success') {
                    showSuccessPopup(result.message || 'Password reset successfully!');
                    setTimeout(() => {
                        window.location.href = result.redirect || '/login-page';
                    }, 3000);
                } else {
                    output.textContent = result.message || 'Reset failed';
                }
            } catch (error) {
                output.textContent = 'Network error: ' + error.message;
                console.error('Reset password error:', error);
            }
        }
    });

    // Lock Form
    document.getElementById('lock-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const password = document.getElementById('lock-password')?.value;
        const fileInput = document.getElementById('lock-file');
        const file = fileInput?.files[0];
        const output = document.getElementById('lock-output');
        if (output) {
            if (!file || !password) {
                output.textContent = 'Please enter a password and select a file';
                output.className = 'error';
                return;
            }
            const formData = new FormData();
            formData.append('password', password);
            formData.append('file', file);

            try {
                const response = await fetch('/lock', { method: 'POST', body: formData });
                const result = await response.json();
                if (result.status === 'success') {
                    showSuccessPopup(`File locked: ${result.file_name}`);
                    fileInput.value = ''; // Reset file input
                    output.className = 'success';
                    output.textContent = '';
                } else {
                    output.textContent = result.message || 'Failed to lock file';
                    output.className = 'error';
                }
            } catch (error) {
                output.textContent = 'Network error';
                console.error('Lock error:', error);
            }
        }
    });

    // List Form with Modal
    document.getElementById('list-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const password = document.getElementById('list-password')?.value;
        const output = document.getElementById('list-output');
        if (output) {
            if (!password) {
                output.textContent = 'Please enter a password';
                output.className = 'error';
                return;
            }
            const formData = new FormData();
            formData.append('password', password);

            try {
                const response = await fetch('/list', { method: 'POST', body: formData });
                const result = await response.json();
                if (result.status === 'success') {
                    showFileListModal(result.files, password);
                } else {
                    output.textContent = result.message || 'Failed to list files';
                    output.className = 'error';
                }
            } catch (error) {
                output.textContent = 'Network error';
                console.error('List error:', error);
            }
        }
    });

    // Recycle Form with Modal
    document.getElementById('recycle-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const password = document.getElementById('recycle-password')?.value;
        const output = document.getElementById('recycle-output');
        if (output) {
            if (!password) {
                output.textContent = 'Please enter a password';
                output.className = 'error';
                return;
            }
            const formData = new FormData();
            formData.append('password', password);

            try {
                const response = await fetch('/recycle', { method: 'POST', body: formData });
                const result = await response.json();
                const list = document.getElementById('recycle-list');
                if (list) {
                    list.innerHTML = '';
                    if (result.status === 'success') {
                        showRecycleBinModal(result.files, password);
                    } else {
                        list.textContent = result.message || 'Failed to view recycle bin';
                    }
                } else {
                    output.textContent = 'File restored successfully'; // Changed from error message
                    output.className = 'success';
                }
            } catch (error) {
                output.textContent = 'Network error';
                console.error('Recycle error:', error);
            }
        }
    });

    // Retrieve File
    window.retrieveFile = async (fileName, password) => {
        const formData = new FormData();
        formData.append('password', password);
        formData.append('file_name', fileName);
        const output = document.getElementById('list-output');

        try {
            const response = await fetch('/retrieve', { method: 'POST', body: formData });
            if (output) {
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = fileName.replace('.enc', '');
                    a.click();
                    output.textContent = 'File retrieved successfully';
                    output.className = 'success';
                } else {
                    const result = await response.json();
                    output.textContent = result.message || 'Failed to retrieve file';
                    output.className = 'error';
                }
            }
        } catch (error) {
            if (output) {
                output.textContent = 'Network error';
                output.className = 'error';
            }
            console.error('Retrieve error:', error);
        }
    };

    // Delete File
    window.deleteFile = async (fileName, password) => {
        const formData = new FormData();
        formData.append('password', password);
        formData.append('file_name', fileName);
        const output = document.getElementById('list-output');

        try {
            const response = await fetch('/delete', { method: 'POST', body: formData });
            const result = await response.json();
            if (output) {
                if (result.status === 'success') {
                    output.textContent = 'File deleted successfully';
                    output.className = 'success';
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                    document.getElementById('list-form')?.dispatchEvent(new Event('submit'));
                } else {
                    output.textContent = result.message || 'Failed to delete file';
                    output.className = 'error';
                }
            }
        } catch (error) {
            if (output) {
                output.textContent = 'Network error';
                output.className = 'error';
            }
            console.error('Delete error:', error);
        }
    };

    // Restore File
    window.restoreFile = async (fileName, password) => {
        const formData = new FormData();
        formData.append('password', password);
        formData.append('file_name', fileName);
        const output = document.getElementById('recycle-output');

        try {
            const response = await fetch('/restore', { method: 'POST', body: formData });
            const result = await response.json();
            if (output) {
                if (result.status === 'success') {
                    output.textContent = 'File restored successfully';
                    output.className = 'success';
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                    document.getElementById('recycle-form')?.dispatchEvent(new Event('submit'));
                } else {
                    output.textContent = result.message || 'Failed to restore file';
                    output.className = 'error';
                }
            }
        } catch (error) {
            if (output) {
                output.textContent = 'Network error';
                output.className = 'error';
            }
            console.error('Restore error:', error);
        }
    };

    // Logout Handler
    document.querySelectorAll('a[href="/logout"]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            fetch('/logout', { method: 'GET' })
                .then(response => response.text())
                .then(() => window.location.href = '/')
                .catch(error => console.error('Logout error:', error));
        });
    });

    // Show Success Popup
    function showSuccessPopup(message) {
        let popup = document.createElement('div');
        popup.className = 'success-popup';
        popup.innerHTML = `
            <div class="popup-content">
                <i class="fas fa-check-circle"></i>
                <p>${message}</p>
                <button class="close-popup">Close</button>
            </div>
        `;
        document.body.appendChild(popup);

        document.querySelector('.close-popup')?.addEventListener('click', () => {
            document.body.removeChild(popup);
        });

        setTimeout(() => {
            if (document.body.contains(popup)) {
                document.body.removeChild(popup);
            }
        }, 3000);
    }

    // Show File List Modal
    function showFileListModal(files, password) {
        let modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Your Files</h3>
                <ul id="modal-file-list"></ul>
                <button class="close-modal">Close</button>
            </div>
        `;
        document.body.appendChild(modal);

        const list = modal.querySelector('#modal-file-list');
        if (files.length > 0) {
            files.forEach(file => {
                const li = document.createElement('li');
                li.innerHTML = `${file} 
                    <div>
                        <button onclick="retrieveFile('${file}', '${password}')">Retrieve</button>
                        <button onclick="deleteFile('${file}', '${password}')">Delete</button>
                    </div>`;
                list.appendChild(li);
            });
        } else {
            list.textContent = 'No files found.';
        }

        document.querySelector('.close-modal').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
    }

    // Show Recycle Bin Modal
    function showRecycleBinModal(files, password) {
        let modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Recycle Bin</h3>
                <ul id="modal-recycle-list"></ul>
                <button class="close-modal">Close</button>
            </div>
        `;
        document.body.appendChild(modal);

        const list = modal.querySelector('#modal-recycle-list');
        if (files.length > 0) {
            files.forEach(file => {
                const li = document.createElement('li');
                li.innerHTML = `${file} <button onclick="restoreFile('${file}', '${password}')">Restore</button>`;
                list.appendChild(li);
            });
        } else {
            list.textContent = 'No files in recycle bin.';
        }

        document.querySelector('.close-modal').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
    }
});