
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
        switch (error.response.status) {
            case 401:
                // axios.interceptors.response.eject(resInterceptor)

                const refreshCall = getNewToken(error)

                const id = axios.interceptors.request.use(
                    config => refreshCall.then(() => config)
                )

                return refreshCall.then(() => {
                    return axios.request(error.config)
                }).catch(error => {
                    return Promise.reject(error)
                }).finally(() => {
                    axios.interceptors.request.eject(id)
                    // axios.interceptors.response.use(resInterceptor)
                })

        }
        return Promise.reject(error)
    }
)

const getNewToken = error => axios.post('/tokens').then(res => {
    localStorage.setItem('token', res.data['token'])
    error.config.headers.Authorization = 'Bearer ' + res.data['token']
    return Promise.resolve()
})

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

const getScrollFactor = (eid) => {
    return document.getElementById(eid).childElementCount / 20
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

function getFeedPosts() {
    const down = window.pageYOffset + window.innerHeight >= document.documentElement.scrollHeight - 200 * getScrollFactor('ListContent')
    if (!down) {return}
    const next = localStorage.getItem('posts:next')
    if (next == 'null') {return}
    let lc = document.getElementById('ListContent')
    axios.get(next).then(
        res => {
            res.data['posts'].map(p => createPostCard(p)).map(
                html => lc.insertAdjacentHTML('beforeend', html)
            )
            localStorage.setItem('posts:next', res.data['next'])
            let sc = document.getElementsByClassName('showComment')
            Array.from(sc, e => e.addEventListener('click', initComments))
        }
    )
}

function getFeedTweets() {
    const down = window.pageYOffset + window.innerHeight >= document.documentElement.scrollHeight - 200 * getScrollFactor('ListContent')
    if (!down) {return}
    const next = localStorage.getItem('tweets:next')
    if (next == 'null') {return}
    let lc = document.getElementById('ListContent')
    axios.get(next).then(
        res => {
            res.data['tweets'].map(t => createTweetCard(t)).map(
                html => lc.insertAdjacentHTML('beforeend', html)
            )
            localStorage.setItem('tweets:next', res.data['next'])
            let sc = document.getElementsByClassName('showComment')
            Array.from(sc, e => e.addEventListener('click', initComments))
        }
    )
}

function getFeedComments() {
    const down = this.scrollTop + this.clientHeight >= this.scrollHeight - 200 * getScrollFactor('ListComment')
    if (!down) {return}
    const next = localStorage.getItem('comments:next')
    if (next == 'null') {return}
    let lc = document.getElementById('ListComment')
    axios.get(next).then(
        res => {
            res.data['comments'].map(c => createCommentCard(c)).map(
                html => lc.insertAdjacentHTML('beforeend', html)
            )
            localStorage.setItem('comments:next', res.data['next'])
        }
    )
}

const scrollPost = _.throttle(getFeedPosts, 300)
const scrollTweet = _.throttle(getFeedTweets, 300)
const scrollComment = _.throttle(getFeedComments, 300)

function addCommentListener() {
    let sc = document.getElementById('ScrollContent')
    sc.addEventListener('scroll', scrollComment)
}

function removeCommentListener() {
    let sc = document.getElementById('ScrollContent')
    sc.removeEventListener('scroll', scrollComment)
}

function initFeedPosts() {
    window.removeEventListener('scroll', scrollTweet)
    window.addEventListener('scroll', scrollPost)
    let lc = document.getElementById('ListContent')
    lc.innerHTML = ""
    axios.get('/posts').then(
        res => {
            res.data['posts'].map(p => createPostCard(p)).map(
                html => lc.insertAdjacentHTML('beforeend', html)
            )
            localStorage.setItem('posts:next', res.data['next'])
            let sc = document.getElementsByClassName('showComment')
            Array.from(sc, e => e.addEventListener('click', initComments))
        }
    )
}

function initFeedTweets() {
    window.removeEventListener('scroll', scrollPost)
    window.addEventListener('scroll', scrollTweet)
    let lc = document.getElementById('ListContent')
    lc.innerHTML = ""
    axios.get('/tweets').then(
        res => {
            res.data['tweets'].map(t => createTweetCard(t)).map(
                html => lc.insertAdjacentHTML('beforeend', html)
            )
            localStorage.setItem('tweets:next', res.data['next'])
            let sc = document.getElementsByClassName('showComment')
            Array.from(sc, e => e.addEventListener('click', initComments))
        }
    )
}


function initHotPosts() {

}

function getHotPosts() {

}

function ping() {
    alert('aaa')
}

function initComments() {
    let mt = document.getElementById('ModalTitle')
    let lc = document.getElementById('ListComment')
    let card = this.closest('.ui.card')
    mt.innerText = card.querySelector('a.header').innerText
    lc.innerHTML = ""
    item_id = card.getAttribute('item-id')
    item_md = card.getAttribute('item-md')
    axios.get(`/${item_md}/${item_id}/comments`).then(
        res => {
            res.data['comments'].map(c => createCommentCard(c)).map(
                html => lc.insertAdjacentHTML('beforeend', html)
            )
            localStorage.setItem('comments:next', res.data['next'])
            $('.ui.small.modal').modal({
                onShow: addCommentListener,
                onHidden: removeCommentListener
            })
            $('.ui.small.modal').modal('show')
        }
    )
}

const createPostCard = (post) => `
<div class="ui fluid card noBorderCard" item-id="${post.id}" item-md="posts">
  <div class="content">
    <div class="right floated meta">${post.create_time}</div>
    <a class="header" href="${post.url}" target="_blank">${post.title}</a>
    <a class="meta" href="${post.author.bio}" target="_blank">
        ${post.author.username}
    </a>
    <div class="description">
      <p>${post.body}</p>
    </div>
  </div>
  <div class="extra content">
    <span class="left floated iconItem" data-inverted data-tooltip="Likes" data-position="top left" data-variation="mini">
        <i class="${post.css.like} link icon"></i>${post.like_count}
    </span>
    <span class="left floated iconItem" data-inverted data-tooltip="Comments" data-position="top left" data-variation="mini">
        <i class="comment link icon showComment"></i>${post.comment_count}
    </span>
    <span class="left floated iconItem" data-inverted data-tooltip="Favorites" data-position="top left" data-variation="mini">
        <i class="${post.css.star} link icon"></i>${post.collect_count}
    </span>
    <span class="left floated" data-inverted data-tooltip="Share" data-position="top left" data-variation="mini">
        <i class="paper plane link icon"></i>
    </span>
    <span class="right floated" data-inverted data-tooltip="Favorites" data-position="top left" data-variation="mini">
        <i class="${post.css.star} icon"></i>${post.collect_count}
    </span>
  </div>
</div>
<div class="ui divider"></div>
`

const createTweetCard = (tweet) => `
<div class="ui fluid card noBorderCard" item-id="${tweet.id}" item-md="tweets">
  <div class="content">
    <div class="right floated meta">${tweet.create_time}</div>
    <a class="header" href="${tweet.author.bio}" target="_blank">
        ${tweet.author.username}
    </a>
    <div class="description">
      <p>${tweet.body}</p>
    </div>
  </div>
  <div class="extra content">
    <span class="left floated iconItem" data-inverted data-tooltip="Likes" data-position="top left" data-variation="mini">
        <i class="${tweet.css.like} link icon"></i>${tweet.like_count}
    </span>
    <span class="left floated iconItem" data-inverted data-tooltip="Comments" data-position="top left" data-variation="mini">
        <i class="comment link icon showComment"></i>${tweet.comment_count}
    </span>
    <span class="left floated iconItem" data-inverted data-tooltip="Favorites" data-position="top left" data-variation="mini">
        <i class="${tweet.css.star} link icon"></i>${tweet.collect_count}
    </span>
    <span class="left floated" data-inverted data-tooltip="Share" data-position="top left" data-variation="mini">
        <i class="paper plane link icon"></i>
    </span>
    <span class="right floated" data-inverted data-tooltip="Favorites" data-position="top left" data-variation="mini">
        <i class="${tweet.css.star} icon"></i>${tweet.collect_count}
    </span>
  </div>
</div>
<div class="ui divider"></div>
`

const createCommentCard = (comment) => `
<div class="comment">
    <a class="avatar">
      <img src="${comment.author.avatar}">
    </a>
    <div class="content">
      <a class="author" href="${comment.author.bio}" target="_blank">
        ${comment.author.username}
      </a>
      ${comment.parent ? `<i class="at icon"></i><a class="author" href="${comment.parent.author.bio}" target="_blank">${comment.parent.author.username}</a>` : ''}
      <div class="metadata">
        <span class="date">${comment.create_time}</span>
        <span data-inverted data-tooltip="Likes" data-position="right center" data-variation="mini">
            <i class="${comment.css.like} link icon"></i>${comment.like_count}
        </span>
      </div>
      <div class="text">
        ${comment.body}
      </div>
      <div class="actions">
        <a class="reply">Reply</a>
      </div>
    </div>
</div>
`
