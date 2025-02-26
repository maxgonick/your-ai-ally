export function clickOutside(node: HTMLElement) {
    // the node has been mounted in the DOM

    window.addEventListener('click', handleClick);

    function handleClick(e: MouseEvent) {
        if (!node.contains(e.target as Node)) {
            node.dispatchEvent(new CustomEvent('outsideclick'))
        }
    }

    return {
        destroy() {
            // the node has been removed from the DOM
            window.removeEventListener('click', handleClick)
        }
    };
} 