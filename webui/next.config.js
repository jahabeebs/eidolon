const NodePolyfillPlugin = require('node-polyfill-webpack-plugin');

module.exports = {
    webpack: (config, { isServer }) => {
        config.resolve.fallback = {
            ...config.resolve.fallback,
            url: require.resolve('url/'),
        };

        config.plugins.push(new NodePolyfillPlugin());

        return config;
    },
};