"use strict";

const request = require("request");

exports.handler = (event, context, callback) => {
    request.post(process.env.URL, callback);
};
