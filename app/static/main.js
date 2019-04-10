// close message
$('.message .close')
  .on('click', function () {
    $(this)
      .closest('.message')
      .transition('fade');
});

$('.special.card .image').dimmer({
  on: 'hover'
});

$(document)
  .ready(function () {
    // dropdown menu
    $('.ui.menu .ui.dropdown').dropdown({
      on: 'hover'
    });

    // active menu
    $('.ui.menu a.item')
      .on('click', function () {
        $(this)
          .addClass('active')
          .siblings()
          .removeClass('active');
      });

    // fix menu when passed
    $('.masthead')
      .visibility({
        once: false,
        onBottomPassed: function () {
          $('.fixed.menu').transition('fade in');
        },
        onBottomPassedReverse: function () {
          $('.fixed.menu').transition('fade out');
        }
      });

    // create sidebar and attach to menu open
    $('.ui.sidebar')
      .sidebar('attach events', '.toc.item');

    // form validation
    $('.ui.form')
      .form({
        fields: {
          email: {
            identifier: 'email',
            rules: [{
                type: 'empty',
                prompt: 'Please enter your e-mail'
              },
              {
                type: 'email',
                prompt: 'Please enter a valid e-mail'
              }
            ]
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
              }
            ]
          }
        }
      });
  });
