let onboardingController = function() {
    const STORAGE_KEY_ACTIVE = 'onboarding_tour_active';
    const STORAGE_KEY_STEP = 'onboarding_tour_step';

    const steps = [
        {
            page: '/',
            selector: '.navbar-nav',
            placement: 'bottom',
            title: 'Welcome to Simpli Budget',
            body: 'This nav bar is how you get everywhere: Budget for your monthly overview, Transactions to search everything, and Categories, Tags, Rules, and Accounts to manage the pieces that power your budget.'
        },
        {
            page: '/',
            selector: '#next-month',
            placement: 'left',
            title: 'Move between months',
            body: 'Use these arrows to look back at past months or ahead to upcoming ones.'
        },
        {
            page: '/',
            selector: 'a.list-group-item[href*="/budget/category/"]',
            placement: 'top',
            title: 'Your categories',
            body: 'Each row is a budget category for the month. Click one to see its transactions and how it compares to what you budgeted.'
        },
        {
            page: '/transactions/search',
            selector: '.dt-buttons',
            placement: 'bottom',
            title: 'Search & export',
            body: 'Filter using the boxes at the bottom of each column (date, name, account, category, tags), then use Export to download everything matching your filters — not just what’s on screen.'
        },
        {
            page: '/categories',
            selector: '#new-category-form',
            placement: 'bottom',
            title: 'Create categories',
            body: 'Add a new category here, choose which group it belongs to, and set a monthly budget amount.'
        },
        {
            page: '/tags',
            selector: '#new-tag-form',
            placement: 'bottom',
            title: 'Create tags',
            body: 'Tags label transactions across categories, e.g. for a specific trip or shared project.'
        },
        {
            page: '/rules',
            selector: '#new-rule',
            placement: 'bottom',
            title: 'Automate categorization',
            body: 'Create a rule to automatically assign a category to future transactions that match checks you define.'
        },
        {
            page: '/accounts',
            selector: '#add-account-btn',
            placement: 'bottom',
            title: 'Connect a bank account',
            body: 'Click here to securely link a bank account via Plaid so your transactions import automatically.'
        }
    ];

    let popover = null;

    let getStepIndex = function() {
        let stored = parseInt(localStorage.getItem(STORAGE_KEY_STEP), 10);
        return isNaN(stored) ? 0 : stored;
    };

    let setStepIndex = function(index) {
        localStorage.setItem(STORAGE_KEY_STEP, String(index));
    };

    let isTourActive = function() {
        return localStorage.getItem(STORAGE_KEY_ACTIVE) === 'true';
    };

    let setTourActive = function(active) {
        if (active) {
            localStorage.setItem(STORAGE_KEY_ACTIVE, 'true');
        } else {
            localStorage.removeItem(STORAGE_KEY_ACTIVE);
            localStorage.removeItem(STORAGE_KEY_STEP);
        }
    };

    let clearHighlight = function() {
        document.querySelectorAll('.onboarding-highlight').forEach(function(el) {
            el.classList.remove('onboarding-highlight');
        });
    };

    let removeResumeButton = function() {
        let resumeBtn = document.getElementById('onboarding-resume-btn');
        if (resumeBtn) {
            resumeBtn.remove();
        }
    };

    let hidePopover = function() {
        clearHighlight();
        if (popover) {
            popover.dispose();
            popover = null;
        }
    };

    let completeOnboarding = function() {
        setTourActive(false);
        hidePopover();
        removeResumeButton();
        let banner = document.getElementById('onboarding-banner');
        if (banner) {
            banner.remove();
        }
        fetch('/api/onboarding/complete', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            }
        }).catch(function(e) { console.log(e); });
    };

    let showPopover = function(target, step, index) {
        hidePopover();
        removeResumeButton();
        target.classList.add('onboarding-highlight');
        target.scrollIntoView({behavior: 'smooth', block: 'center'});

        let isLast = index === steps.length - 1;
        let content = `
            <div class="mb-2">${step.body}</div>
            <div class="d-flex justify-content-between">
                <div>
                    <button type="button" class="btn btn-sm btn-outline-secondary" id="onboarding-back-btn" ${index === 0 ? 'disabled' : ''}>Back</button>
                    <button type="button" class="btn btn-sm btn-link text-danger" id="onboarding-tour-skip-btn">Skip</button>
                </div>
                <button type="button" class="btn btn-sm btn-primary" id="onboarding-next-btn">${isLast ? 'Finish' : 'Next'}</button>
            </div>
        `;

        target.addEventListener('shown.bs.popover', function onShown() {
            target.removeEventListener('shown.bs.popover', onShown);
            let popoverEls = document.querySelectorAll('.popover');
            let popoverEl = popoverEls[popoverEls.length - 1];
            if (!popoverEl) {
                return;
            }
            let backBtn = popoverEl.querySelector('#onboarding-back-btn');
            let nextBtn = popoverEl.querySelector('#onboarding-next-btn');
            let skipBtn = popoverEl.querySelector('#onboarding-tour-skip-btn');
            if (backBtn) {
                backBtn.addEventListener('click', function() { goToStep(index - 1); });
            }
            if (nextBtn) {
                nextBtn.addEventListener('click', function() { goToStep(index + 1); });
            }
            if (skipBtn) {
                skipBtn.addEventListener('click', completeOnboarding);
            }
        });

        popover = new bootstrap.Popover(target, {
            title: step.title,
            content: content,
            html: true,
            sanitize: false,
            trigger: 'manual',
            placement: step.placement || 'bottom',
            customClass: 'onboarding-popover'
        });
        popover.show();
    };

    let showResumeButton = function(index) {
        removeResumeButton();
        let container = document.getElementById('onboarding-resume-container');
        if (!container) {
            return;
        }
        let btn = document.createElement('button');
        btn.id = 'onboarding-resume-btn';
        btn.type = 'button';
        btn.className = 'btn btn-sm btn-primary';
        btn.textContent = 'Resume Tour';
        btn.addEventListener('click', function() {
            new Loader().show();
            window.location.href = steps[index].page;
        });
        container.appendChild(btn);
    };

    let goToStep = function(index) {
        if (index < 0) {
            return;
        }
        if (index >= steps.length) {
            completeOnboarding();
            return;
        }

        let step = steps[index];
        if (step.page !== window.location.pathname) {
            setStepIndex(index);
            new Loader().show();
            window.location.href = step.page;
            return;
        }

        let target = document.querySelector(step.selector);
        if (!target || target.offsetParent === null || target.disabled) {
            goToStep(index + 1);
            return;
        }

        setStepIndex(index);
        showPopover(target, step, index);
    };

    let startTour = function() {
        setTourActive(true);
        let banner = document.getElementById('onboarding-banner');
        if (banner) {
            banner.remove();
        }
        goToStep(0);
    };

    document.addEventListener('DOMContentLoaded', function() {
        let banner = document.getElementById('onboarding-banner');

        if (isTourActive()) {
            if (banner) {
                banner.remove();
            }
            let stepIndex = getStepIndex();
            if (steps[stepIndex] && steps[stepIndex].page === window.location.pathname) {
                goToStep(stepIndex);
            } else {
                showResumeButton(stepIndex);
            }
            return;
        }

        if (banner) {
            document.getElementById('onboarding-start-btn').addEventListener('click', startTour);
            document.getElementById('onboarding-skip-btn').addEventListener('click', completeOnboarding);
        }
    });
}();
