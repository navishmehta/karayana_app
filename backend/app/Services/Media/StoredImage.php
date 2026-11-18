<?php

namespace App\Services\Media;

/** Paths (on the media disk) of an uploaded image and its thumbnail. */
final readonly class StoredImage
{
    public function __construct(public string $path, public string $thumbPath) {}
}
