// event handler for updating allocated beds value of number input
u('.num-beds-allocated-range').handle('change, input', (event) => {
    let input = u(event.target).closest('tr').find('.num-beds-allocated');
    // update value of number input
    input.first().value = event.target.value;
    // update sum
    let bedSum = Number(u('#beds-allocated-sum').html());
    let previousValue = Number(input.data('previous'));
    let newValue = Number(event.target.value);
    u('#beds-allocated-sum').html(bedSum + newValue - previousValue);
    // set new previous value
    input.data('previous', newValue);
});
// event handler for updating allocated beds value of range input
u('.num-beds-allocated').handle('change', (event) => {
    // update value of range input
    u(event.target).closest('tr').find('.num-beds-allocated-range').first().value = event.target.value;
    // update sum
    let bedSum = Number(u('#beds-allocated-sum').html());
    let previousValue = Number(u(event.target).data('previous'));
    let newValue = Number(event.target.value);
    u('#beds-allocated-sum').html(bedSum + newValue - previousValue);
    // set new previous value
    u(event.target).data('previous', newValue);
});
// update previous value (for sum calculation)
u('.num-beds-allocated').handle('focus', (event) => {
    u(event.target).data('previous', event.target.value);
});
// update previous values on page load
u(document).handle("DOMContentLoaded", () => {
    u('.num-beds-allocated').trigger('focus');
});