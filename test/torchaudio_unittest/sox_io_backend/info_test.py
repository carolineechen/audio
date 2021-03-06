import io
import itertools
import tarfile

from parameterized import parameterized
from torchaudio.backend import sox_io_backend
from torchaudio._internal import module_utils as _mod_utils

from torchaudio_unittest.common_utils import (
    TempDirMixin,
    HttpServerMixin,
    PytorchTestCase,
    skipIfNoExec,
    skipIfNoExtension,
    skipIfNoModule,
    get_asset_path,
    get_wav_data,
    save_wav,
    sox_utils,
)
from .common import (
    name_func,
)


if _mod_utils.is_module_available("requests"):
    import requests


@skipIfNoExec('sox')
@skipIfNoExtension
class TestInfo(TempDirMixin, PytorchTestCase):
    @parameterized.expand(list(itertools.product(
        ['float32', 'int32', 'int16', 'uint8'],
        [8000, 16000],
        [1, 2],
    )), name_func=name_func)
    def test_wav(self, dtype, sample_rate, num_channels):
        """`sox_io_backend.info` can check wav file correctly"""
        duration = 1
        path = self.get_temp_path('data.wav')
        data = get_wav_data(dtype, num_channels, normalize=False, num_frames=duration * sample_rate)
        save_wav(path, data, sample_rate)
        info = sox_io_backend.info(path)
        assert info.sample_rate == sample_rate
        assert info.num_frames == sample_rate * duration
        assert info.num_channels == num_channels
        assert info.bits_per_sample == sox_utils.get_bit_depth(dtype)

    @parameterized.expand(list(itertools.product(
        ['float32', 'int32', 'int16', 'uint8'],
        [8000, 16000],
        [4, 8, 16, 32],
    )), name_func=name_func)
    def test_wav_multiple_channels(self, dtype, sample_rate, num_channels):
        """`sox_io_backend.info` can check wav file with channels more than 2 correctly"""
        duration = 1
        path = self.get_temp_path('data.wav')
        data = get_wav_data(dtype, num_channels, normalize=False, num_frames=duration * sample_rate)
        save_wav(path, data, sample_rate)
        info = sox_io_backend.info(path)
        assert info.sample_rate == sample_rate
        assert info.num_frames == sample_rate * duration
        assert info.num_channels == num_channels
        assert info.bits_per_sample == sox_utils.get_bit_depth(dtype)

    @parameterized.expand(list(itertools.product(
        [8000, 16000],
        [1, 2],
        [96, 128, 160, 192, 224, 256, 320],
    )), name_func=name_func)
    def test_mp3(self, sample_rate, num_channels, bit_rate):
        """`sox_io_backend.info` can check mp3 file correctly"""
        duration = 1
        path = self.get_temp_path('data.mp3')
        sox_utils.gen_audio_file(
            path, sample_rate, num_channels,
            compression=bit_rate, duration=duration,
        )
        info = sox_io_backend.info(path)
        assert info.sample_rate == sample_rate
        # mp3 does not preserve the number of samples
        # assert info.num_frames == sample_rate * duration
        assert info.num_channels == num_channels
        assert info.bits_per_sample == 0  # bit_per_sample is irrelevant for compressed formats

    @parameterized.expand(list(itertools.product(
        [8000, 16000],
        [1, 2],
        list(range(9)),
    )), name_func=name_func)
    def test_flac(self, sample_rate, num_channels, compression_level):
        """`sox_io_backend.info` can check flac file correctly"""
        duration = 1
        path = self.get_temp_path('data.flac')
        sox_utils.gen_audio_file(
            path, sample_rate, num_channels,
            compression=compression_level, duration=duration,
        )
        info = sox_io_backend.info(path)
        assert info.sample_rate == sample_rate
        assert info.num_frames == sample_rate * duration
        assert info.num_channels == num_channels
        assert info.bits_per_sample == 24  # FLAC standard

    @parameterized.expand(list(itertools.product(
        [8000, 16000],
        [1, 2],
        [-1, 0, 1, 2, 3, 3.6, 5, 10],
    )), name_func=name_func)
    def test_vorbis(self, sample_rate, num_channels, quality_level):
        """`sox_io_backend.info` can check vorbis file correctly"""
        duration = 1
        path = self.get_temp_path('data.vorbis')
        sox_utils.gen_audio_file(
            path, sample_rate, num_channels,
            compression=quality_level, duration=duration,
        )
        info = sox_io_backend.info(path)
        assert info.sample_rate == sample_rate
        assert info.num_frames == sample_rate * duration
        assert info.num_channels == num_channels
        assert info.bits_per_sample == 0  # bit_per_sample is irrelevant for compressed formats

    @parameterized.expand(list(itertools.product(
        [8000, 16000],
        [1, 2],
        [16, 32],
    )), name_func=name_func)
    def test_sphere(self, sample_rate, num_channels, bits_per_sample):
        """`sox_io_backend.info` can check sph file correctly"""
        duration = 1
        path = self.get_temp_path('data.sph')
        sox_utils.gen_audio_file(path, sample_rate, num_channels, duration=duration, bit_depth=bits_per_sample)
        info = sox_io_backend.info(path)
        assert info.sample_rate == sample_rate
        assert info.num_frames == sample_rate * duration
        assert info.num_channels == num_channels
        assert info.bits_per_sample == bits_per_sample

    @parameterized.expand(list(itertools.product(
        ['float32', 'int32', 'int16', 'uint8'],
        [8000, 16000],
        [1, 2],
    )), name_func=name_func)
    def test_amb(self, dtype, sample_rate, num_channels):
        """`sox_io_backend.info` can check amb file correctly"""
        duration = 1
        path = self.get_temp_path('data.amb')
        bits_per_sample = sox_utils.get_bit_depth(dtype)
        sox_utils.gen_audio_file(
            path, sample_rate, num_channels,
            bit_depth=bits_per_sample, duration=duration)
        info = sox_io_backend.info(path)
        assert info.sample_rate == sample_rate
        assert info.num_frames == sample_rate * duration
        assert info.num_channels == num_channels
        assert info.bits_per_sample == bits_per_sample

    def test_amr_nb(self):
        """`sox_io_backend.info` can check amr-nb file correctly"""
        duration = 1
        num_channels = 1
        sample_rate = 8000
        path = self.get_temp_path('data.amr-nb')
        sox_utils.gen_audio_file(
            path, sample_rate=sample_rate, num_channels=num_channels, bit_depth=16,
            duration=duration)
        info = sox_io_backend.info(path)
        assert info.sample_rate == sample_rate
        assert info.num_frames == sample_rate * duration
        assert info.num_channels == num_channels
        assert info.bits_per_sample == 0


@skipIfNoExtension
class TestInfoOpus(PytorchTestCase):
    @parameterized.expand(list(itertools.product(
        ['96k'],
        [1, 2],
        [0, 5, 10],
    )), name_func=name_func)
    def test_opus(self, bitrate, num_channels, compression_level):
        """`sox_io_backend.info` can check opus file correcty"""
        path = get_asset_path('io', f'{bitrate}_{compression_level}_{num_channels}ch.opus')
        info = sox_io_backend.info(path)
        assert info.sample_rate == 48000
        assert info.num_frames == 32768
        assert info.num_channels == num_channels
        assert info.bits_per_sample == 0  # bit_per_sample is irrelevant for compressed formats


@skipIfNoExtension
class TestLoadWithoutExtension(PytorchTestCase):
    def test_mp3(self):
        """Providing `format` allows to read mp3 without extension

        libsox does not check header for mp3

        https://github.com/pytorch/audio/issues/1040

        The file was generated with the following command
            ffmpeg -f lavfi -i "sine=frequency=1000:duration=5" -ar 16000 -f mp3 test_noext
        """
        path = get_asset_path("mp3_without_ext")
        sinfo = sox_io_backend.info(path, format="mp3")
        assert sinfo.sample_rate == 16000
        assert sinfo.bits_per_sample == 0  # bit_per_sample is irrelevant for compressed formats


@skipIfNoExtension
@skipIfNoExec('sox')
class TestFileObject(TempDirMixin, PytorchTestCase):
    @parameterized.expand([
        ('wav', 32),
        ('mp3', 0),
        ('flac', 24),
        ('vorbis', 0),
        ('amb', 32),
    ])
    def test_fileobj(self, ext, bits_per_sample):
        """Querying audio via file object works"""
        sample_rate = 16000
        num_channels = 2
        duration = 3
        format_ = ext if ext in ['mp3'] else None
        path = self.get_temp_path(f'test.{ext}')

        sox_utils.gen_audio_file(
            path, sample_rate, num_channels=2,
            duration=duration)

        with open(path, 'rb') as fileobj:
            sinfo = sox_io_backend.info(fileobj, format_)

        assert sinfo.sample_rate == sample_rate
        assert sinfo.num_channels == num_channels
        if ext not in ['mp3', 'vorbis']:  # these container formats do not have length info
            assert sinfo.num_frames == sample_rate * duration
        assert sinfo.bits_per_sample == bits_per_sample

    def _test_bytesio(self, ext, bits_per_sample, duration):
        sample_rate = 16000
        num_channels = 2
        format_ = ext if ext in ['mp3'] else None
        path = self.get_temp_path(f'test.{ext}')

        sox_utils.gen_audio_file(
            path, sample_rate, num_channels=2,
            duration=duration)

        with open(path, 'rb') as file_:
            fileobj = io.BytesIO(file_.read())
        sinfo = sox_io_backend.info(fileobj, format_)

        assert sinfo.sample_rate == sample_rate
        assert sinfo.num_channels == num_channels
        if ext not in ['mp3', 'vorbis']:  # these container formats do not have length info
            assert sinfo.num_frames == sample_rate * duration
        assert sinfo.bits_per_sample == bits_per_sample

    @parameterized.expand([
        ('wav', 32),
        ('mp3', 0),
        ('flac', 24),
        ('vorbis', 0),
        ('amb', 32),
    ])
    def test_bytesio(self, ext, bits_per_sample):
        """Querying audio via ByteIO object works"""
        self._test_bytesio(ext, bits_per_sample, duration=3)

    @parameterized.expand([
        ('wav', 32),
        ('mp3', 0),
        ('flac', 24),
        ('vorbis', 0),
        ('amb', 32),
    ])
    def test_bytesio_tiny(self, ext, bits_per_sample):
        """Querying audio via ByteIO object works for small data"""
        self._test_bytesio(ext, bits_per_sample, duration=1 / 1600)

    @parameterized.expand([
        ('wav', 32),
        ('mp3', 0),
        ('flac', 24),
        ('vorbis', 0),
        ('amb', 32),
    ])
    def test_tarfile(self, ext, bits_per_sample):
        """Querying compressed audio via file-like object works"""
        sample_rate = 16000
        num_channels = 2
        duration = 3
        format_ = ext if ext in ['mp3'] else None
        audio_file = f'test.{ext}'
        audio_path = self.get_temp_path(audio_file)
        archive_path = self.get_temp_path('archive.tar.gz')

        sox_utils.gen_audio_file(
            audio_path, sample_rate, num_channels=num_channels, duration=duration)

        with tarfile.TarFile(archive_path, 'w') as tarobj:
            tarobj.add(audio_path, arcname=audio_file)
        with tarfile.TarFile(archive_path, 'r') as tarobj:
            fileobj = tarobj.extractfile(audio_file)
            sinfo = sox_io_backend.info(fileobj, format=format_)

        assert sinfo.sample_rate == sample_rate
        assert sinfo.num_channels == num_channels
        if ext not in ['mp3', 'vorbis']:  # these container formats do not have length info
            assert sinfo.num_frames == sample_rate * duration
        assert sinfo.bits_per_sample == bits_per_sample


@skipIfNoExtension
@skipIfNoExec('sox')
@skipIfNoModule("requests")
class TestFileObjectHttp(HttpServerMixin, PytorchTestCase):
    @parameterized.expand([
        ('wav', 32),
        ('mp3', 0),
        ('flac', 24),
        ('vorbis', 0),
        ('amb', 32),
    ])
    def test_requests(self, ext, bits_per_sample):
        """Querying compressed audio via requests works"""
        sample_rate = 16000
        num_channels = 2
        duration = 3
        format_ = ext if ext in ['mp3'] else None
        audio_file = f'test.{ext}'
        audio_path = self.get_temp_path(audio_file)

        sox_utils.gen_audio_file(
            audio_path, sample_rate, num_channels=num_channels, duration=duration)

        url = self.get_url(audio_file)
        with requests.get(url, stream=True) as resp:
            sinfo = sox_io_backend.info(resp.raw, format=format_)

        assert sinfo.sample_rate == sample_rate
        assert sinfo.num_channels == num_channels
        if ext not in ['mp3', 'vorbis']:  # these container formats do not have length info
            assert sinfo.num_frames == sample_rate * duration
        assert sinfo.bits_per_sample == bits_per_sample
