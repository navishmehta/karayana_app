<?php

namespace App\Notifications;

use Illuminate\Bus\Queueable;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

/** Sent in the user's own language (User::preferredLocale). */
class PasswordResetCodeNotification extends Notification
{
    use Queueable;

    public function __construct(private readonly string $code) {}

    public function via(object $notifiable): array
    {
        return ['mail'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        $minutes = config('kirana.auth.reset_code_ttl_minutes');

        return (new MailMessage)
            ->subject(__('notifications.password_reset.subject', ['app' => config('app.name')]))
            ->greeting(__('notifications.password_reset.greeting', ['name' => $notifiable->name]))
            ->line(__('notifications.password_reset.intro'))
            ->line('**'.$this->code.'**')
            ->line(__('notifications.password_reset.expiry', ['minutes' => $minutes]))
            ->line(__('notifications.password_reset.ignore'));
    }
}
