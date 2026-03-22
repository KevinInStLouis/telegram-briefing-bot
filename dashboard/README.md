# Frontend

This template is a classic client-side-only React app. 

## `index.html`

The **entrypoint** for the frontend is `/frontend/index.html`. This is the HTML page that is returned at the root from `/backend/index.ts`.

This HTML file imports `/frontend/style.css` from `/public/style.css` and `/frontend/favicon.svg` from `/frontend/favicon.svg`. Everything in `/frontend/` is mapped to `/public` by `/backend/index.ts`. This is just a convention. You could import & serve everything out of the same folder name.

This HTML file has a `<div id="root"></div>`, which is where we mount the React app.

This HTML file imports `/frontend/index.tsx` from `/public/index.tsx`, which is the **entrypoint** for all frontend JavaScript, including all the React. It is not a problem that it imports a file with a `.tsx` extension becaues browsers ignore file extensions. They only pay attention to content-types, which is great, because all these files will be returned as transpiled JS with the appropriate JS content type by [stevekrouse/utils/serve-public](https://www.val.town/x/stevekrouse/utils/branch/main/code/serve-public/README.md).)

## `index.tsx`

This file is the **entrypoint** for frontend JavaScript. It imports the React app from `/frontend/components/App.tsx` and mounts it on `<div id="root"></div>`.

It also looks for *bootstrapped* JSON data at `window.__INITIAL_DATA`, and passes that only to the `<App />`.

## `favicon.svg`

As of this writing Val Town only supports text files, which is why the favicon is an SVG and not an .ico or any other binary image format. If you need binary file storage, check out [Blob Storage](https://docs.val.town/std/blob/).

## `components/`

This directory is where the React components are stored. They're pretty standard client-side React components.
