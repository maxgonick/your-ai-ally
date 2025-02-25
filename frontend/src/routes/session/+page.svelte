<script lang="ts">
	import * as Resizable from '$lib/components/ui/resizable';
	import { Textarea } from '$lib/components/ui/textarea';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
</script>

<div class="flex h-screen w-screen items-center justify-center">
	<Resizable.PaneGroup direction="horizontal" class="max-w-full border">
		<Resizable.Pane defaultSize={25} minSize={25} class="relative">
			<div
				class="bg-background absolute bottom-0 z-10 flex h-32 w-full items-center justify-center border-t p-4"
			>
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>Open</DropdownMenu.Trigger>
					<DropdownMenu.Content>
						<DropdownMenu.Group>
							<DropdownMenu.DropdownMenuGroupHeading
								>My Account</DropdownMenu.DropdownMenuGroupHeading
							>
							<DropdownMenu.Separator />
							<DropdownMenu.Item>Profile</DropdownMenu.Item>
							<DropdownMenu.Item>Billing</DropdownMenu.Item>
							<DropdownMenu.Item>Team</DropdownMenu.Item>
							<DropdownMenu.Item>Subscription</DropdownMenu.Item>
						</DropdownMenu.Group>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
				<Textarea class="h-full resize-none" placeholder="Enter prompt here" />
			</div>
		</Resizable.Pane>
		<Resizable.Handle />
		<Resizable.Pane defaultSize={75} minSize={50}>
			<div class="flex h-full items-center justify-center p-6">
				<span class="font-semibold">Two</span>
			</div>
		</Resizable.Pane>
	</Resizable.PaneGroup>
</div>
