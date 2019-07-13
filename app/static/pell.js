(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
        typeof define === 'function' && define.amd ? define(['exports'], factory) :
        (factory((global.pell = {})));
}(this, (function (exports) {
    'use strict';

    var _extends = Object.assign || function (target) {
        for (var i = 1; i < arguments.length; i++) {
            var source = arguments[i];
            for (var key in source) {
                if (Object.prototype.hasOwnProperty.call(source, key)) {
                    target[key] = source[key];
                }
            }
        }
        return target;
    };

    var defaultParagraphSeparatorString = 'defaultParagraphSeparator';
    var formatBlock = 'formatBlock';
    var addEventListener = function addEventListener(parent, type, listener) {
        return parent.addEventListener(type, listener);
    };
    var appendChild = function appendChild(parent, child) {
        return parent.appendChild(child);
    };
    var createElement = function createElement(tag) {
        return document.createElement(tag);
    };
    var queryCommandState = function queryCommandState(command) {
        return document.queryCommandState(command);
    };
    var queryCommandValue = function queryCommandValue(command) {
        return document.queryCommandValue(command);
    };

    var exec = function exec(command) {
        var value = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;
        return document.execCommand(command, false, value);
    };

    var defaultActions = {
        bold: {
            icon: '<i class="bold icon"></i>',
            title: 'Bold',
            state: function state() {
                return queryCommandState('bold');
            },
            result: function result() {
                return exec('bold');
            }
        },
        italic: {
            icon: '<i class="italic icon"></i>',
            title: 'Italic',
            state: function state() {
                return queryCommandState('italic');
            },
            result: function result() {
                return exec('italic');
            }
        },
        underline: {
            icon: '<i class="underline icon"></i>',
            title: 'Underline',
            state: function state() {
                return queryCommandState('underline');
            },
            result: function result() {
                return exec('underline');
            }
        },
        strikethrough: {
            icon: '<i class="strikethrough icon"></i>',
            title: 'Strike-through',
            state: function state() {
                return queryCommandState('strikeThrough');
            },
            result: function result() {
                return exec('strikeThrough');
            }
        },
        heading1: {
            icon: '<i class="heading icon"><sub>1</sub></i>',
            title: 'Heading 1',
            result: function result() {
                return exec(formatBlock, '<h1>');
            }
        },
        heading2: {
            icon: '<i class="heading icon"><sub>2</sub></i>',
            title: 'Heading 2',
            result: function result() {
                return exec(formatBlock, '<h2>');
            }
        },
        heading3: {
            icon: '<i class="heading icon"><sub>3</sub></i>',
            title: 'Heading 3',
            result: function result() {
                return exec(formatBlock, '<h3>');
            }
        },
        paragraph: {
            icon: '<i class="paragraph icon"></i>',
            title: 'Paragraph',
            result: function result() {
                return exec(formatBlock, '<p>');
            }
        },
        quote: {
            icon: '<i class="quote left icon"></i>',
            title: 'Quote',
            result: function result() {
                return exec(formatBlock, '<blockquote>');
            }
        },
        olist: {
            icon: '<i class="list ol icon"></i>',
            title: 'Ordered List',
            result: function result() {
                return exec('insertOrderedList');
            }
        },
        ulist: {
            icon: '<i class="list ul icon"></i>',
            title: 'Unordered List',
            result: function result() {
                return exec('insertUnorderedList');
            }
        },
        code: {
            icon: '<i class="code icon"></i>',
            title: 'Code',
            result: function result() {
                return exec(formatBlock, '<pre>');
            }
        },
        line: {
            icon: '<i class="ellipsis horizontal icon"></i>',
            title: 'Horizontal Line',
            result: function result() {
                return exec('insertHorizontalRule');
            }
        },
        link: {
            icon: '<i class="linkify icon"></i>',
            title: 'Link',
            result: function result() {
                var url = window.prompt('Enter the link URL');
                if (url) exec('createLink', url);
            }
        },
        image: {
            icon: '<i class="image icon"></i>',
            title: 'Image',
            result: function result() {
                var url = window.prompt('Enter the image URL');
                if (url) exec('insertImage', url);
            }
        },
        redo: {
            icon: '<i class="redo icon"></i>',
            title: 'Redo',
            result: function result() {
                return exec('redo');
            }
        },
        undo: {
            icon: '<i class="undo icon"></i>',
            title: 'Undo',
            result: function result() {
                return exec('undo');
            }
        },
        removeformat: {
            icon: '<i class="eraser icon"></i>',
            title: 'Remove-format',
            result: function result() {
                return exec('removeFormat');
            }
        },
    };

    var defaultClasses = {
        actionbar: 'ui fluid icon buttons',
        button: 'ui basic button',
        content: 'pellContent',
        selected: 'blue'
    };

    var init = function init(settings) {
        var actions = settings.actions ? settings.actions.map(function (action) {
            if (typeof action === 'string') return defaultActions[action];
            else if (defaultActions[action.name]) return _extends({}, defaultActions[action.name], action);
            return action;
        }) : Object.keys(defaultActions).map(function (action) {
            return defaultActions[action];
        });

        var classes = _extends({}, defaultClasses, settings.classes);

        var defaultParagraphSeparator = settings[defaultParagraphSeparatorString] || 'p';

        var actionbar = createElement('div');
        actionbar.className = classes.actionbar;
        appendChild(settings.element, actionbar);

        var content = settings.element.content = createElement('div');
        content.contentEditable = true;
        content.className = classes.content;
        content.oninput = function (_ref) {
            var firstChild = _ref.target.firstChild;

            if (firstChild && firstChild.nodeType === 3) exec(formatBlock, '<' + defaultParagraphSeparator + '>');
            else if (content.innerHTML === '<br>') content.innerHTML = '';
            settings.onChange(content.innerHTML);
        };
        content.onkeydown = function (event) {
            if (event.key === 'Enter' && queryCommandValue(formatBlock) === 'blockquote') {
                setTimeout(function () {
                    return exec(formatBlock, '<' + defaultParagraphSeparator + '>');
                }, 0);
            }
        };
        appendChild(settings.element, content);

        actions.forEach(function (action) {
            var button = createElement('button');
            button.className = classes.button;
            button.innerHTML = action.icon;
            button.title = action.title;
            button.onclick = function () {
                return action.result() && content.focus();
            };

            if (action.state) {
                var handler = function handler() {
                    return button.firstChild.classList[action.state() ? 'add' : 'remove'](classes.selected);
                };
                addEventListener(content, 'keyup', handler);
                addEventListener(content, 'mouseup', handler);
                addEventListener(button, 'click', handler);
            }

            appendChild(actionbar, button);
        });

        if (settings.styleWithCSS) exec('styleWithCSS');
        exec(defaultParagraphSeparatorString, defaultParagraphSeparator);

        return settings.element;
    };

    var pell = {
        exec: exec,
        init: init
    };

    exports.exec = exec;
    exports.init = init;
    exports['default'] = pell;

    Object.defineProperty(exports, '__esModule', {
        value: true
    });

})));
