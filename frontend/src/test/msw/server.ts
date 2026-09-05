import { setupServer } from "msw/node";

import { defaultHandlers } from "./handlers";

export const mockApiServer = setupServer(...defaultHandlers);
