<?php

namespace App\Services\Media;

use App\Enums\ErrorCode;
use App\Enums\MediaFolder;
use App\Exceptions\ApiException;
use Illuminate\Contracts\Filesystem\Filesystem;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Intervention\Image\Drivers\Gd\Driver;
use Intervention\Image\Encoders\WebpEncoder;
use Intervention\Image\ImageManager;
use Intervention\Image\Interfaces\ImageInterface;
use Throwable;

/**
 * Stores uploaded images safely: the upload is decoded and re-encoded to WebP
 * (full size + thumbnail), so the original bytes — including EXIF/GPS or any hidden payload — are never kept.
 */
class ImageService
{
    public function store(UploadedFile $file, MediaFolder $folder): StoredImage
    {
        $config = config('kirana.media');
        $name = $folder->value.'/'.Str::uuid();

        try {
            $manager = ImageManager::usingDriver(Driver::class, strip: true, decodeAnimation: false);
            $full = $manager->decodePath($file->getRealPath())->scaleDown(width: $config['full_width']);
            $thumb = (clone $full)->scaleDown(width: $config['thumb_width']);
        } catch (Throwable) {
            throw new ApiException(ErrorCode::InvalidImage);
        }

        $stored = new StoredImage("{$name}.webp", "{$name}_thumb.webp");
        $this->disk()->put($stored->path, $this->encode($full), 'public');
        $this->disk()->put($stored->thumbPath, $this->encode($thumb), 'public');

        return $stored;
    }

    public function delete(?string ...$paths): void
    {
        $paths = array_filter($paths);
        if ($paths) {
            $this->disk()->delete($paths);
        }
    }

    public function url(?string $path): ?string
    {
        return $path ? $this->disk()->url($path) : null;
    }

    private function encode(ImageInterface $image): string
    {
        return $image->encode(new WebpEncoder(quality: config('kirana.media.webp_quality'), strip: true))->toString();
    }

    private function disk(): Filesystem
    {
        return Storage::disk(config('kirana.media.disk'));
    }
}
