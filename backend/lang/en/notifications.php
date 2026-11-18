<?php

return [
    'password_reset' => [
        'subject' => ':app password reset code',
        'greeting' => 'Hello :name,',
        'intro' => 'Use this code in the app to reset your password:',
        'expiry' => 'The code expires in :minutes minutes.',
        'ignore' => 'If you did not ask for this, you can ignore this email.',
    ],
];
