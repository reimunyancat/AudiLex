import { createBrowserRouter } from "react-router-dom";
import Home from "./pages/Home";
import AudioDetail from "./pages/AudioDetail";

const router = createBrowserRouter([
	{ path: '/', element: <Home /> },
	{ path: '/view/:id', element: <AudioDetail /> },
]);

export default router;