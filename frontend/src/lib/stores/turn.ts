import { writable } from "svelte/store";

export const turn = writable<'idle' | 'starting' | 'running' | 'stopping'>('idle');


