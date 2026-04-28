
export function debounce<
	Fn extends (this: any, ...args: any[]) => any
>(
	func: Fn,
	wait: number,
	immediate: boolean = false
): (...args: Parameters<Fn>) => void | undefined {
	let timeout: number | undefined;
	return function(this: ThisParameterType<Fn>, ...args: Parameters<Fn>) {
		const callNow = immediate && !timeout;
		window.clearTimeout(timeout);
		timeout = window.setTimeout(() => {
			timeout = undefined;
			if (!immediate) {
				func.apply(this, args);
			}
		}, wait);
		if (callNow) func.apply(this, args);
	}
}
