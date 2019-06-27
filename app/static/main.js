// import axios from 'axios'

// 通用设置
axios.defaults.baseURL = 'http://127.0.0.1:5000/api'
axios.defaults.headers.common['Content-Type'] = 'application/json'

// 请求拦截器
axios.interceptors.request.use(
    config => {
        const token = 'Bearer ' + localStorage.getItem('token')
        config.headers.Authorization = token
        return config
    }, error => {
        return Promise.reject(error)
    }
)

// 响应拦截器
axios.interceptors.response.use(
    response => {
        localStorage.setItem('token', response.data['token'])
        return response
    }, error => {
        return Promise.reject(error)
    }
)

const emailValidator = {
    identifier: 'email',
    rules: [{
            type: 'empty',
            prompt: 'Please enter your email'
        },
        {
            type: 'email',
            prompt: 'Please enter a valid email'
        }
    ]
}
const passwordValidator = {
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

function closeMessage() {
    $('.message .close').on('click', function () {
        $(this).closest('.message').transition('fade')
    })
}

function dimmerCard() {
    $('.blurring.dimmable.image').dimmer({
        on: 'hover'
    })
}

function dropdownMenu() {
    $('.ui.menu .ui.dropdown').dropdown({
        on: 'hover'
    })
}

function activeItem() {
    $('.ui.menu a.item').on('click', function () {
        $(this).addClass('active').siblings().removeClass('active')
    })
}

function validateForm() {
    $('.ui.form').form({
        fields: {
            email: emailValidator,
            password: passwordValidator
        }
    })
}

function initBase() {
    closeMessage()
    dimmerCard()
    dropdownMenu()
    activeItem()
    validateForm()
}

function editProfile() {
    let inputs = this.closest('.ui.form').getElementsByTagName('input')
    let user_id = localStorage.getItem('user:id')
    let data = {}
    for (let i of inputs) {
        data[i.name] = i.value.trim()
    }
    axios.put(`/users/${user_id}`, data)
    .then(res => console.log(res))
}

function initFeedPosts() {
    let lc = document.getElementById('ListContent')
    lc.innerHTML = ""
    axios.get('/posts').then(
        res => {
            res['data']['posts'].map(p => createPostCard(p)).map(
                html => lc.insertAdjacentHTML('beforeend', html)
            )
            localStorage.setItem('posts:next', res['data']['next'])
            let sc = document.getElementsByClassName('showComment')
            Array.from(sc, e => e.addEventListener('click', showComment))
        }
    )
}

function getFeedPosts() {
    const down = window.pageYOffset + window.innerHeight >= document.documentElement.scrollHeight
    if (!down) {return}
    const next = localStorage.getItem('posts:next')
    if (next == 'null') {return}
    let lc = document.getElementById('ListContent')
    axios.get(next).then(
        res => {
            res['data']['posts'].map(p => createPostCard(p)).map(
                html => lc.insertAdjacentHTML('beforeend', html)
            )
            localStorage.setItem('posts:next', res['data']['next'])
            let sc = document.getElementsByClassName('showComment')
            Array.from(sc, e => e.addEventListener('click', showComment))
        }
    )
}

function initFollowingPosts() {

}

function initHotPosts() {

}

function showComment() {
    $('.ui.modal').modal('show')
}


let createPostCard = (post) => `
<div class="ui fluid card noBorderCard">
  <div class="content">
    <div class="right floated meta">${post.create_time}</div>
    <div class="header">${post.title}</div>
    <div class="meta">${post.author.username}</div>
    <div class="description">
      <p>${post.body}</p>
    </div>
  </div>
  <div class="extra content">
    <span class="left floated iconItem" title="Like">
        <i class="${post.css.like} link icon"></i>${post.like_count}
    </span>
    <span class="left floated iconItem" title="Comment">
        <i class="comment link icon showComment"></i>${post.comment_count}
    </span>
    <span class="left floated iconItem" title="Favorite">
        <i class="${post.css.star} link icon"></i>${post.collect_count}
    </span>
    <span class="left floated" title="Share">
        <i class="paper plane link icon"></i>
    </span>
    <span class="right floated" title="Favorite">
        <i class="${post.css.star} icon"></i>${post.collect_count}
    </span>
  </div>
</div>
<div class="ui divider"></div>
`
