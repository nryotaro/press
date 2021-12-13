
module.exports = {
    verbose: true ,
    testMatch: [
        "**/test/**/*.test.js"
    ],
    transform: {
        '^.+\\.js$': 'babel-jest',
      },
      moduleFileExtensions: ['js']
};