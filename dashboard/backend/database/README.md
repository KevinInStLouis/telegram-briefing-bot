# Database

This app uses [Val Town SQLite](https://docs.val.town/std/sqlite/) to manage data. Every Val Town account comes with a free SQLite database, hosted on [Turso](https://turso.tech/). This folder is broken up into two files:

* `migrations.ts` - code to set up the database tables the app needs
* `queries.ts` - functions to run queries against those tables, which are imported and used in the main Hono server in `/backend/index.ts`

## Migrations

In `backend/database/migrations.ts`, this app creates a new SQLite table `reactHonoStarter_messages` to store messages. 

This "migration" runs once on every app startup because it's imported in `index.ts`. You can comment this line out for a slight (30ms) performance improvement on cold starts. It's left in so that users who fork this project will have the migration run correctly.

SQLite has much more limited support for altering existing tables as compared to other databases. Often it's easier to create new tables with the schema you want, and then copy the data over. Happily LLMs are quite good at those sort of database operations, but please reach out in the [Val Town Discord](https://discord.com/invite/dHv45uN5RY) if you need help.

## Queries

The queries file is where running the migrations happen in this app. It'd also be reasonable for that to happen in index.ts, or as is said above, for that line to be commented out, and only run when actual changes are made to your database schema.

The queries file exports functions to get and write data. It relies on shared types and data imported from the `/shared` directory.
