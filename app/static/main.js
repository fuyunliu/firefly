const email_validator = {
    identifier: 'email',
    rules: [{
        type: 'empty',
        prompt: 'Please enter your email'
    },
    {
        type: 'email',
        prompt: 'Please enter a valid email'
    }]
}
const password_validator = {
    identifier: 'password',
    rules: [{
        type: 'empty',
        prompt: 'Please enter your password'
    },
    {
        type: 'length[8]',
        prompt: 'Your password must be at least 8 characters'
    }]
}

class Firefly {

    close_message() {
        $('.message .close').on('click', function () { $(this).closest('.message').transition('fade'); });
    }

    dimmer_card() {
        $('.blurring.dimmable.image').dimmer({ on: 'hover' });
    }

    dropdown_menu() {
        $('.ui.menu .ui.dropdown').dropdown({ on: 'hover' });
    }

    active_item() {
        $('.ui.menu a.item').on('click', function () { $(this).addClass('active').siblings().removeClass('active'); });
    }

    fixed_menu() {
        $('.mainNavbar').visibility({
            once: false,
            onBottomPassed: function () { $('.fixed.menu').transition('fade in'); },
            onBottomPassedReverse: function () { $('.fixed.menu').transition('fade out'); }
        })
    }

    show_sidebar() {
        $('.ui.sidebar').sidebar('attach events', '.toc.item');
    }

    validate_form() {
        $('.ui.form').form({
            fields: {
                email: email_validator,
                password: password_validator
            }
        })
    }

    edit_profile(url, token) {
        $('.editProfileForm .ui.button').on('click', function () {
            let ele = this.closest('.fields').querySelector('input');
            let data = {}
            data[ele.name] = ele.value.trim()
            fetch(url, {
                method: 'PUT',
                body: JSON.stringify(data),
                headers: new Headers({
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                })
            }).then(res => res.json())
                .catch(error => console.error('Error:', error))
                .then(res => console.log('Success:', res))

        })
    }

    get_all_posts(url, token) {
        fetch(url, {
            method: 'GET',
            headers: new Headers({
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            })
        }).then(res => res.json())
            .catch(error => console.error('Error:', error))
            .then(res => console.log('Success:', res))
    }


}
