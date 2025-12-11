<template>
    <div class="body">
        <div class="container">
            <div class="card">
                <h1>Welcome to Influencer Engagement and Sponsorship Platform</h1>
                <p>A platform to connect influencers and sponsors</p>
                <!-- Buttons linking to Login and Register pages -->
                <router-link to="/login" class="button">Login</router-link>
                <router-link to="/register" class="button">Register</router-link>
            </div>
        </div>
    </div>
</template>

<script>
export default {
  name: 'HomePage'
}
</script>

<style scoped>

.body {
    min-width: 100%;
    min-height: 100vh;
    background: linear-gradient(120deg, #A9F1DF , #FFBBBB);
}

/* Styles for card elements */
.card {
    background: #ffffff;
    border-radius: 10px;
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin-bottom: 20px;
    min-height: 200px; /* Ensures the card has a minimum height */
    margin-top: 0; /* Removes top margin */
}

/* Container styling for main content */
.container {
    width: 35%;
    min-height: 250px; /* Ensures container has a minimum height */
    max-width: 1200px;
    margin: 30px auto;
    padding: 25px;
    justify-content: center;
    border-radius: 10px;
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    background: linear-gradient(-225deg, #EA8D8D, #A890FE);
}

/* Button styling with a gradient background and hover effect */
.button {
    display: inline-block;
    padding: 12px 25px;
    margin-top: 15px;
    margin-inline-end: 4px;
    background: linear-gradient(90deg, #667eea, #764ba2);
    color: white;
    text-decoration: none;
    border-radius: 5px;
    transition: background 0.3s ease, transform 0.2s ease;
    cursor: pointer;
    border: none;
    font-size: 15px;
    font-weight: bold;
}

/* Button hover effect with gradient change and slight lift */
.button:hover {
    background: linear-gradient(90deg, #764ba2, #667eea);
    transform: translateY(-2px);
}

@media (max-width: 430px) {
    .container {
        width: 75%; /* Expands width on tablets and smaller screens */        
        display:flex;
        min-height: 250px; /* Ensures container has a minimum height */
        max-width: 1900px;
        margin: 30px auto;
        padding: 25px;
        justify-content: center;
        border-radius: 10px;
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
        background: linear-gradient(-225deg, #EA8D8D, #A890FE);
    }
}
</style>