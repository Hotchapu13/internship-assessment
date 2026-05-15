/** @type {import('next').NextConfig} */
const nextConfig = {
    allowedDevOrigins: ['192.168.1.189', 'localhost:3000'],
    logging:{
        fetches:{
            fullUrl: true,
        },
    },
};

export default nextConfig;
