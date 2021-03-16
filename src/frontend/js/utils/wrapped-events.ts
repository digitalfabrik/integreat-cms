/* 
 * We sometimes need a way to detach all event listeners of a certain type from an element.
 * This helpers keep track on what has been added and is therefore able to remove all those
 */

 const eventMap = new Map<Element, Map<keyof HTMLElementEventMap, EventHandlerNonNull[]>>();

 /**
  * Wrapper around Element.addEventListener that keeps track of the handlers so you can use the off function
  * 
  * @param el the element that should rect on `event`
  * @param event the event name
  * @param handler the listener to attach
  */
export function on(el: Element, event: keyof HTMLElementEventMap, handler: EventHandlerNonNull) {
    if(!eventMap.has(el)) {
        eventMap.set(el, new Map());
    }
    if(!eventMap.get(el).get(event)) {
        eventMap.get(el).set(event, []);
    }
    eventMap.get(el).get(event).push(handler);
    el.addEventListener(event, handler);
}

/**
 * Detaches all event listers of a certain type
 * @param el the element that should not react on the events anymore
 * @param events the event or events to detach
 */
export function off(el: Element, events: keyof HTMLElementEventMap|(keyof HTMLElementEventMap)[]) {
    if(!Array.isArray(events)) {
        events = [events];
    }
    events.forEach(event => {
        if(!eventMap.has(el) || !eventMap.get(el).has(event)) {
            return;
        }
        const attachedHandlers = eventMap.get(el).get(event);
        attachedHandlers.forEach(handler => {
            el.removeEventListener(event, handler);
        })
    })
}