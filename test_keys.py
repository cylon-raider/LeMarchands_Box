from vpython import *
import time

scene.title = """
<script>
window.test_key = function(down) {
    var e = new KeyboardEvent(down ? 'keydown' : 'keyup', {key: 'left'});
    document.dispatchEvent(e);
}
</script>
<button onmousedown="test_key(true)" onmouseup="test_key(false)">Test Key (JS Dispatch)</button>
"""

def hk(evt):
    print("Python caught keydown:", evt.key)

def ku(evt):
    print("Python caught keyup:", evt.key)

scene.bind('keydown', hk)
scene.bind('keyup', ku)

while True:
    rate(10)
