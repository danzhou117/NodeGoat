"use strict";

const MongoClient = require("mongodb").MongoClient;
const UserDAO = require("../../app/data/user-dao").UserDAO;

const [userName, firstName, lastName, password, email] = process.argv.slice(2);

MongoClient.connect(process.env.MONGODB_URI, (err, db) => {
    if (err) {
        console.error(err);
        process.exit(1);
    }
    new UserDAO(db).addUser(userName, firstName, lastName, password, email, (err) => {
        if (err) {
            console.error(err);
            process.exit(1);
        }
        db.close(() => process.exit(0));
    });
});
