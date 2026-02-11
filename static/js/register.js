let intlTelInputInstance;
let countriesData = {};
let provincesData = {};

document.addEventListener('DOMContentLoaded', async function() {
    // Load countries and provinces data
    try {
        const countriesResponse = await fetch('/static/data/countries.json');
        countriesData = await countriesResponse.json();
        
        const provincesResponse = await fetch('/static/data/provinces.json');
        provincesData = await provincesResponse.json();
    } catch (error) {
        console.error('Error loading data:', error);
    }

    const phoneEl = document.getElementById('id_phone');
    const countryEl = document.getElementById('id_country');
    const provinceEl = document.getElementById('id_province');
    const cityEl = document.getElementById('id_city');

    // Get initial values - use data-initial attribute, fallback to 'Ecuador'
    let initialCountry = countryEl?.dataset?.initial?.trim() || 'Ecuador';
    const initialProvince = provinceEl?.dataset?.initial?.trim() || '';
    const initialCity = cityEl?.dataset?.initial?.trim() || '';

    // Initialize intl-tel-input
    if (phoneEl) {
        // Get country code from initial country name
        let countryCode = countriesData.find(c => c.name === initialCountry)?.code || 'EC';
        
        intlTelInputInstance = window.intlTelInput(phoneEl, {
            initialCountry: countryCode.toLowerCase(),
            preferredCountries: ['ec', 'us', 'mx', 'co', 'es'],
            separateDialCode: false,
            utilsScript: 'https://cdn.jsdelivr.net/npm/intl-tel-input@23.8.0/build/js/utils.min.js'
        });

        // After intl-tel-input is initialized, sync with country select
        setTimeout(() => {
            if (intlTelInputInstance && initialCountry) {
                const countryCode = countriesData.find(c => c.name === initialCountry)?.code;
                if (countryCode) {
                    intlTelInputInstance.setCountry(countryCode.toLowerCase());
                }
            }
        }, 500);

        // Listen to country changes in intl-tel-input
        phoneEl.addEventListener('countrychange', function() {
            const countryData = intlTelInputInstance.getSelectedCountryData();
            if (countryData) {
                const countryCode = countryData.iso2.toUpperCase();
                // Find country name by code
                const countryName = countriesData.find(c => c.code === countryCode)?.name;
                if (countryName) {
                    countryEl.value = countryName;
                    updateProvinces(countryName);
                }
            }
        });
    }

    // Populate initial countries select
    function populateCountries() {
        if (!countryEl) return;
        countryEl.innerHTML = '';
        countriesData.forEach(country => {
            const opt = document.createElement('option');
            opt.value = country.name;
            opt.textContent = country.name;
            if (country.name === initialCountry) {
                opt.selected = true;
            }
            countryEl.appendChild(opt);
        });
    }

    function updateProvinces(countryName) {
        if (!provinceEl) return;
        const countryData = provincesData[countriesData.find(c => c.name === countryName)?.code];
        provinceEl.innerHTML = '';
        const def = document.createElement('option');
        def.value = '';
        def.textContent = 'Seleccione una provincia';
        provinceEl.appendChild(def);

        if (countryData && countryData.provinces) {
            Object.keys(countryData.provinces).forEach(p => {
                const opt = document.createElement('option');
                opt.value = p;
                opt.textContent = p;
                // Restore selected province if it matches initial
                if (p === initialProvince && initialProvince) {
                    opt.selected = true;
                }
                provinceEl.appendChild(opt);
            });
        }
        
        // Only clear cities if we're changing countries (not on initial load)
        if (countryName !== initialCountry || !initialProvince) {
            cityEl.innerHTML = '';
            const defCity = document.createElement('option');
            defCity.value = '';
            defCity.textContent = 'Seleccione una ciudad';
            cityEl.appendChild(defCity);
        }
    }

    function updateCities(countryName, provinceName) {
        if (!cityEl) return;
        const countryCode = countriesData.find(c => c.name === countryName)?.code;
        const cities = provincesData[countryCode]?.provinces[provinceName] || [];
        
        cityEl.innerHTML = '';
        const def = document.createElement('option');
        def.value = '';
        def.textContent = 'Seleccione una ciudad';
        cityEl.appendChild(def);

        cities.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            if (c === initialCity && initialCity) {
                opt.selected = true;
            }
            cityEl.appendChild(opt);
        });
    }

    // Populate countries and set initial values
    populateCountries();
    updateProvinces(initialCountry);
    if (initialProvince) {
        updateCities(initialCountry, initialProvince);
    }

    // Country change event
    countryEl?.addEventListener('change', function(e) {
        const countryName = e.target.value;
        updateProvinces(countryName);
        // Update intl-tel-input country
        const countryCode = countriesData.find(c => c.name === countryName)?.code;
        if (countryCode && intlTelInputInstance) {
            intlTelInputInstance.setCountry(countryCode.toLowerCase());
        }
    });

    // Province change event
    provinceEl?.addEventListener('change', function(e) {
        const province = e.target.value;
        const country = countryEl.value;
        updateCities(country, province);
    });

    // Password client-side validation
    const pwEl = document.getElementById('id_password') || document.querySelector('input[name="password"]');
    const pwConfirmEl = document.getElementById('id_password_confirm') || document.querySelector('input[name="password_confirm"]');
    const criteria = {
        length: document.getElementById('pc-length'),
        upper: document.getElementById('pc-upper'),
        lower: document.getElementById('pc-lower'),
        digit: document.getElementById('pc-digit'),
        symbol: document.getElementById('pc-symbol')
    };
    const pwMatch = document.getElementById('pw-match');

    function checkPassword(pw) {
        if (!pw) return;
        criteria.length.style.color = pw.length >= 8 ? 'green' : '#9CA3AF';
        criteria.upper.style.color = /[A-Z]/.test(pw) ? 'green' : '#9CA3AF';
        criteria.lower.style.color = /[a-z]/.test(pw) ? 'green' : '#9CA3AF';
        criteria.digit.style.color = /\d/.test(pw) ? 'green' : '#9CA3AF';
        criteria.symbol.style.color = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(pw) ? 'green' : '#9CA3AF';
    }

    function checkMatch() {
        if (!pwEl || !pwConfirmEl) return;
        if (pwConfirmEl.value && pwEl.value !== pwConfirmEl.value) {
            pwMatch.classList.remove('invisible');
        } else {
            pwMatch.classList.add('invisible');
        }
    }

    pwEl?.addEventListener('input', function(e) {
        checkPassword(e.target.value);
        checkMatch();
    });
    pwConfirmEl?.addEventListener('input', checkMatch);

    // Phone validation on blur (using intl-tel-input)
    phoneEl?.addEventListener('blur', function(e) {
        const isValid = intlTelInputInstance?.isValidNumber();
        const help = document.getElementById('phone-help');
        if (phoneEl.value && !isValid) {
            help.textContent = 'Formato de teléfono inválido';
            help.style.color = 'rgb(220,38,38)';
        } else if (phoneEl.value && isValid) {
            help.textContent = 'Número válido ✓';
            help.style.color = 'rgb(34,197,94)';
        } else {
            help.textContent = 'Formato internacional detectado automáticamente.';
            help.style.color = '#9CA3AF';
        }
    });

});

