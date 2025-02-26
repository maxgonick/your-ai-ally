// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}

	type Command = {
		id: string;
		name: string;
		description: string;
		placeholder: string;
		icon: typeof ArrowRight;
		onSend: (text: string) => Promise<void>;
		enableSend: (text: string) => boolean;
		runningText: string;
	};

	interface Message { role: "User" | "Agent"; content: string; command: Command }


}

export { };
