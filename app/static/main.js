class Firefly {

    close_message() {
        $('.message .close').on('click', function() {$(this).closest('.message').transition('fade');});
    }

    dimmer_card() {
        $('.blurring.dimmable.image').dimmer({on: 'hover'});
    }

    dropdown_menu() {
        $('.ui.menu .ui.dropdown').dropdown({on: 'hover'});
    }

    active_item() {
        $('.ui.menu a.item').on('click', function() {$(this).addClass('active').siblings().removeClass('active');});
    }

    fixed_menu() {
        $('.mainNavbar').visibility({
            once: false,
            onBottomPassed: function() {$('.fixed.menu').transition('fade in');},
            onBottomPassedReverse: function() {$('.fixed.menu').transition('fade out');}
        })
    }

    show_sidebar() {
        $('.ui.sidebar').sidebar('attach events', '.toc.item');
    }

    validate_form() {
        $('.ui.form').form({
            fields: {
                email: {
                    identifier: 'email',
                    rules: [{
                        type: 'empty',
                        prompt: 'Please enter your email'
                    },
                    {
                        type: 'email',
                        prompt: 'Please enter a valid email'
                    }]
                },
                password: {
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
            }
        })
    }

    edit_profile() {
        $('.editProfileForm .ui.button').on('click', function() {
            let ele = this.parentElement.parentElement.querySelector('input');
            let form = document.querySelector('.editProfileForm')
            let url = form.getAttribute('data-url')
            let token = form.getAttribute('data-token')
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


}

$(document).ready(function() {
    var f = new Firefly()
    f.active_item();
    f.close_message();
    f.dimmer_card();
    f.dropdown_menu();
    f.fixed_menu();
    f.show_sidebar();
    f.validate_form();
    f.edit_profile();
})