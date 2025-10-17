// API base URL
const API_BASE = '';

// Form handling
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('profileForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
});

async function handleFormSubmit(event) {
    event.preventDefault();
    
    const submitBtn = document.querySelector('.submit-btn');
    const btnText = document.querySelector('.btn-text');
    const btnLoading = document.querySelector('.btn-loading');
    
    // Show loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    
    try {
        // Get form data
        const formData = new FormData(event.target);
        const profileData = Object.fromEntries(formData.entries());
        
        // Convert numeric fields
        profileData.age = parseInt(profileData.age);
        profileData.rent_budget_min = parseInt(profileData.rent_budget_min);
        profileData.rent_budget_max = parseInt(profileData.rent_budget_max);
        
        // Handle optional social media fields (remove empty values)
        if (!profileData.instagram_link) delete profileData.instagram_link;
        if (!profileData.facebook_link) delete profileData.facebook_link;
        if (!profileData.linkedin_link) delete profileData.linkedin_link;
        if (!profileData.twitter_link) delete profileData.twitter_link;
        
        // Validate budget range
        if (profileData.rent_budget_min > profileData.rent_budget_max) {
            throw new Error('Minimum budget cannot be greater than maximum budget');
        }
        
        // Create request payload
        const requestPayload = {
            user_profile: profileData
        };
        
        // Call matching API
        const response = await fetch('/api/match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestPayload)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to find matches');
        }
        
        const matches = await response.json();
        
        // Store matches in session storage
        sessionStorage.setItem('matches', JSON.stringify(matches));
        
        // Redirect to results page
        window.location.href = '/results';
        
    } catch (error) {
        console.error('Error:', error);
        showMessage('error', `Error: ${error.message}`);
    } finally {
        // Hide loading state
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
}

function showMessage(type, message) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    
    // Insert at the top of the form
    const form = document.getElementById('profileForm');
    form.insertBefore(messageDiv, form.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Utility functions for results page
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function formatDistance(miles) {
    if (miles < 1) {
        return `${Math.round(miles * 5280)} feet away`;
    }
    return `${miles.toFixed(1)} miles away`;
}

// Sample data for testing (remove in production)
const sampleProfiles = [
    {
        name: "Alice Johnson",
        age: 24,
        gender: "Female",
        occupation: "Software Engineer",
        city: "Dallas",
        zip_code: "75201",
        rent_budget_min: 600,
        rent_budget_max: 800,
        sleep_schedule: "Early Bird",
        cleanliness_level: "Very Clean",
        noise_tolerance: "Quiet",
        hobbies: "Reading, hiking, cooking, photography",
        pet_preference: "Either",
        smoking_preference: "No",
        lifestyle_description: "I'm an early riser who enjoys quiet mornings with coffee and books. I love outdoor activities on weekends and prefer a clean, organized living space. I work from home most days and value peace and quiet."
    },
    {
        name: "Bob Smith",
        age: 26,
        gender: "Male",
        occupation: "Marketing Manager",
        city: "Dallas",
        zip_code: "75201",
        rent_budget_min: 700,
        rent_budget_max: 900,
        sleep_schedule: "Flexible",
        cleanliness_level: "Moderately Clean",
        noise_tolerance: "Moderate",
        hobbies: "Gaming, movies, cooking, fitness",
        pet_preference: "Yes",
        smoking_preference: "No",
        lifestyle_description: "I'm a social person who enjoys hosting friends and trying new restaurants. I work regular hours and like to unwind with video games or movies in the evening. I have a dog and love outdoor activities."
    },
    {
        name: "Carol Davis",
        age: 23,
        gender: "Female",
        occupation: "Graduate Student",
        city: "Dallas",
        zip_code: "75202",
        rent_budget_min: 500,
        rent_budget_max: 700,
        sleep_schedule: "Night Owl",
        cleanliness_level: "Relaxed",
        noise_tolerance: "Loud OK",
        hobbies: "Art, music, dancing, yoga",
        pet_preference: "No",
        smoking_preference: "Either",
        lifestyle_description: "I'm a creative person who loves art and music. I often work late into the night on projects and enjoy a more relaxed approach to cleanliness. I love hosting art parties and jam sessions."
    }
];

// Function to populate sample data (for testing)
function populateSampleData() {
    const form = document.getElementById('profileForm');
    if (!form) return;
    
    const sampleProfile = sampleProfiles[Math.floor(Math.random() * sampleProfiles.length)];
    
    Object.keys(sampleProfile).forEach(key => {
        const input = form.querySelector(`[name="${key}"]`);
        if (input) {
            input.value = sampleProfile[key];
        }
    });
}

// Add sample data button for testing (remove in production)
if (window.location.pathname === '/') {
    document.addEventListener('DOMContentLoaded', function() {
        const formContainer = document.querySelector('.form-container');
        if (formContainer) {
            const sampleBtn = document.createElement('button');
            sampleBtn.type = 'button';
            sampleBtn.textContent = 'Fill Sample Data (Testing)';
            sampleBtn.className = 'btn-secondary';
            sampleBtn.style.marginBottom = '20px';
            sampleBtn.onclick = populateSampleData;
            
            const form = document.getElementById('profileForm');
            form.insertBefore(sampleBtn, form.firstChild);
        }
    });
}
