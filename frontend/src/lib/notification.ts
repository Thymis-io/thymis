import { browser } from '$app/environment';
import { invalidate } from '$app/navigation';
import { toast } from '@zerodevx/svelte-toast';
import { fetchWithNotify } from './fetchWithNotify';

// NotificationDataInner = Union["ShouldInvalidate", "FrontendToast", "ImageBuiltNotification"]

// class Notification:
//     data: "NotificationData"
//     creation_time: datetime.datetime
//     last_try: datetime.datetime
//     send_to: list[WebSocket]

//     def __init__(self, message: NotificationDataInner):
//         self.data = NotificationData(inner=message)
//         self.creation_time = datetime.datetime.now()
//         self.last_try = datetime.datetime.max
//         self.send_to = []

//     def recently_tried(self):
//         now = datetime.datetime.now()
//         return now - self.last_try < datetime.timedelta(seconds=1)

//     def can_retry(self):
//         now = datetime.datetime.now()
//         return now - self.creation_time < datetime.timedelta(seconds=5)

// class NotificationData(BaseModel):
//     inner: NotificationDataInner = Field(discriminator="kind")

// class ShouldInvalidate(BaseModel):
//     kind: Literal["should_invalidate"] = "should_invalidate"
//     should_invalidate_paths: list[str]

// class FrontendToast(BaseModel):
//     kind: Literal["frontend_toast"] = "frontend_toast"
//     message: str

// class ImageBuiltNotification(BaseModel):
//     kind: Literal["image_built"] = "image_built"
//     user_session_id: uuid.UUID
//     configuration_id: str
//     image_format: str

export type Notification = {
	inner: ShouldInvalidate | FrontendToast | ImageBuiltNotification;
};

export type ShouldInvalidate = {
	kind: 'should_invalidate';
	should_invalidate_paths: string[];
};

export type FrontendToast = {
	kind: 'frontend_toast';
	message: string;
};

export type ImageBuiltNotification = {
	kind: 'image_built';
	user_session_id: string;
	configuration_id: string;
	image_format: string;
};

let socket: WebSocket | undefined;

export const startNotificationSocket = () => {
	console.log('starting notification socket');
	const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
	socket = new WebSocket(`${scheme}://${window.location.host}/api/notification`);
	socket.onmessage = async (event) => {
		const notification = JSON.parse(event.data) as Notification;
		if (notification.inner.kind === 'frontend_toast') {
			toast.push(notification.inner.message, { pausable: true });
		} else if (notification.inner.kind === 'should_invalidate') {
			const paths = notification.inner.should_invalidate_paths;
			await invalidate((url: URL) => {
				return paths.some((path: string) => url.pathname.startsWith(path));
			});
		} else if (notification.inner.kind === 'image_built') {
			const inner: ImageBuiltNotification = notification.inner;
			if (browser && inner.image_format === 'sd-card-image') {
				const downloadUrl = `/api/download-image?identifier=${inner.configuration_id}`;
				const response = await fetchWithNotify(downloadUrl, { method: 'HEAD' });
				if (response.ok) {
					const a = document.createElement('a');
					a.href = downloadUrl;
					document.body.appendChild(a);
					a.click();
					document.body.removeChild(a);
				}
			}
		} else {
			const _: never = notification.inner;
		}
	};
	socket.onclose = () => {
		console.log('notification socket closed');
		setTimeout(startNotificationSocket, 1000);
	};
};
