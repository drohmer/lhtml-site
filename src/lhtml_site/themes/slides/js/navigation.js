"use strict";

let controlKeyIsPressed = false;
let mouseInsideTableOfContent = false;
let mouseInsideMenu = false;

document.addEventListener('keydown', keyPressed);
document.addEventListener('keyup',keyReleased);
document.addEventListener('wheel', mouseWheel, {passive:true});
document.addEventListener('touchstart', touchStart, {passive:true});
document.addEventListener('touchend', touchEnd, {passive:true});
document.addEventListener('touchcancel', touchCancel, {passive:true});

const menuElement = document.querySelector('#menu');
const tocElement = document.querySelector('#toc');
menuElement.addEventListener('click', menuClick);



function goNext() {
    const linkElement = document.querySelector('#link-next a');
    if(linkElement!=null){
        linkElement.click();
    }
}
function goPrev() {
    const linkElement = document.querySelector('#link-prev a');
    if(linkElement!=null){
        linkElement.click();
    }
}

// The keys that change the slide: the arrows, and Page Down / Page Up that the remote
// controls of presentations send
const NEXT_KEYS = ['ArrowRight', 'ArrowDown', 'PageDown'];
const PREV_KEYS = ['ArrowLeft', 'ArrowUp', 'PageUp'];

function navigate(key) {
    if (NEXT_KEYS.includes(key)) {
        goNext();
        return true;
    }
    if (PREV_KEYS.includes(key)) {
        goPrev();
        return true;
    }
    return false;
}

function keyPressed(event) {

    if (event.key === 'Control') {
        controlKeyIsPressed = true;
    }

    navigate(event.key);

}

function keyReleased(event) {
    if (event.key === 'Control') {
        controlKeyIsPressed = false;
    }
}

function mouseWheel(event) {
    if (mouseInsideMenu === false && controlKeyIsPressed===false) {
        if (event.deltaY < 0) {
            goPrev();
        }
        else if (event.deltaY > 0) {
            goNext();
        }
    }
}


// A horizontal swipe (phone, tablet, touch screen) goes to the next slide
// (to the left) or the previous one (to the right). A swipe is one finger,
// mostly horizontal, short in time; a pinch, a scroll, a page zoomed in,
// and a swipe on what scrolls sideways itself (a code block) or on a video,
// a form or the menu are left to the browser.
const SWIPE_MIN_DISTANCE = 50;      // CSS pixels
const SWIPE_MAX_DURATION = 800;     // ms
let swipeStart = null;

function touchStart(event) {
    if (event.touches.length !== 1 || ownsHorizontalGesture(event.target)) {
        swipeStart = null;
        return;
    }
    const touch = event.touches[0];
    swipeStart = {x: touch.clientX, y: touch.clientY, time: Date.now()};
}

function touchCancel() {
    swipeStart = null;
}

function touchEnd(event) {
    if (swipeStart === null || event.touches.length !== 0) {
        swipeStart = null;
        return;
    }
    const touch = event.changedTouches[0];
    const dx = touch.clientX - swipeStart.x;
    const dy = touch.clientY - swipeStart.y;
    const duration = Date.now() - swipeStart.time;
    swipeStart = null;
    const zoomed = window.visualViewport && window.visualViewport.scale > 1.01;
    if (zoomed || duration > SWIPE_MAX_DURATION
        || Math.abs(dx) < SWIPE_MIN_DISTANCE || Math.abs(dx) < 2 * Math.abs(dy)) {
        return;
    }
    if (dx < 0) {
        goNext();
    }
    else {
        goPrev();
    }
}

function ownsHorizontalGesture(element) {
    for (let e = element; e instanceof Element; e = e.parentElement) {
        if (e.matches('video, audio, input, textarea, select, iframe, #toc, #menu')) {
            return true;
        }
        const overflow = getComputedStyle(e).overflowX;
        if ((overflow === 'auto' || overflow === 'scroll') && e.scrollWidth > e.clientWidth) {
            return true;
        }
    }
    return false;
}


// A demo in an iframe (demo::) takes the keyboard once it is clicked: its page gets the keys,
// not the slide. The slide listens to the keys of its demos, so that the arrows and Page Down /
// Page Up still change the slide; a demo that uses a key for itself calls preventDefault().
// - A demo of the same site: the slide listens in its page, each time it loads.
// - A demo of another site cannot be listened to: it sends postMessage({slide: {key: 'ArrowRight'}}).
window.__lhtmlNavigation = true;   // the slide handles the keys of its demos (slide-controls.js checks it)

function editable(element) {
    return element && element.matches && element.matches('input, textarea, select, [contenteditable]:not([contenteditable="false"])');
}

function listenToFrame(frame) {
    let view = null;
    try {
        view = frame.contentWindow;
        view.document;                          // throws for a page of another site
    }
    catch (error) {
        return;
    }
    if (!view) {
        return;
    }
    // One listener per page of the frame: the window of a frame may be kept when its first
    // (empty) page is replaced, so the previous listener is removed before adding it again.
    // Added after the scripts of the demo, at the end of the propagation: their own listeners
    // run first and may call preventDefault() to keep a key.
    if (view.__lhtmlSlideListener) {
        view.removeEventListener('keydown', view.__lhtmlSlideListener);
    }
    view.__lhtmlSlideListener = (event) => {
        if (event.defaultPrevented || editable(event.target)) {
            return;
        }
        if (NEXT_KEYS.includes(event.key) || PREV_KEYS.includes(event.key)) {
            event.preventDefault();
            navigate(event.key);
        }
    };
    view.addEventListener('keydown', view.__lhtmlSlideListener);
}

function listenToFrames() {
    for (const frame of document.querySelectorAll('iframe')) {
        listenToFrame(frame);
        frame.addEventListener('load', () => listenToFrame(frame));
    }
}
listenToFrames();

window.addEventListener('message', (event) => {
    const message = event.data && event.data.slide;
    if (!message || typeof message.key !== 'string') {
        return;
    }
    const fromFrame = [...document.querySelectorAll('iframe')].some(frame => frame.contentWindow === event.source);
    if (fromFrame) {
        navigate(message.key);
    }
});


function menuClick()
{
    if (tocElement.classList.contains('hidden')) {
        tocElement.classList.remove('hidden');
        tocElement.addEventListener('pointerenter', enterToc);
        tocElement.addEventListener('pointerleave', leaveToc);
    }
    else {
        tocElement.classList.add('hidden');
        tocElement.removeEventListener('pointerenter', enterToc);
        tocElement.removeEventListener('pointerleave', leaveToc);
    }
}

function enterToc(event) {
    mouseInsideMenu = true;
}
function leaveToc(event) {
    mouseInsideMenu = false;
}


