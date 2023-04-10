pkgbase='python-ovos-utils'
pkgname=('python-ovos-utils')
_module='ovos-utils'
pkgver='0.0.30'
pkgrel=1
pkgdesc="collection of simple utilities for use across the OVOS ecosystem"
url="https://github.com/OpenVoiceOS/ovos_utils"
depends=('python')
makedepends=('python-setuptools')
license=('Apache')
arch=('any')
source=("https://files.pythonhosted.org/packages/source/${_module::1}/$_module/${_module/-/_}-$pkgver.tar.gz")
sha256sums=('a2a68f4856c5addf551d0591f32186d3abb4fe4c9f61dd8f83e34d6c137d5e20')

build() {
    cd "${srcdir}/${_module}-${pkgver}"
    python setup.py build
}

package() {
    depends+=()
    cd "${srcdir}/${_module}-${pkgver}"
    python setup.py install --root="${pkgdir}" --optimize=1 --skip-build
}
