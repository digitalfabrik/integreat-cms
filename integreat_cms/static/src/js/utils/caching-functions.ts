export function evaluateOnceDecorator<T>(fn: ()=>T): ()=>T {
	let value: T | null = null;
	// Save whether we computed the value as a separate boolean, in case we ever literally compute null
	let computed = false;
	return (): T => {
		if (!computed) {
			value = fn();
			computed = true;
		}
		return value;
	};
};
