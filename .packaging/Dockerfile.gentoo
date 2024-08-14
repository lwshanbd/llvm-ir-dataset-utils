FROM gentoo/stage3

RUN echo 'FEATURES="-ipc-sandbox -network-sandbox -pid-sandbox -sandbox -usersandbox -usersync -userfetch -userpriv"' >> /etc/portage/make.conf


COPY $CUSTOM_CERT /usr/local/share/ca-certificates/
RUN update-ca-certificates


RUN emerge-webrsync --no-pgp-verify \
    && emerge --update --deep --newuse @world \
    && emerge app-portage/gentoolkit dev-vcs/git sudo vim app-eselect/eselect-python dev-python/pip cmake dev-build/ninja clang

RUN echo 'export PKGDIR=/data/packages' >> ~/.bashrc

RUN echo 'export LLVM_PATH="/usr/lib/llvm/17"' >> ~/.bashrc

RUN echo 'export PATH="${PATH}:${LLVM_PATH}/bin"' >> ~/.bashrc

RUN echo 'export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${LLVM_PATH}/lib:${LLVM_PATH}/lib64"' >> ~/.bashrc

RUN echo 'export MANPATH="${MANPATH}:${LLVM_PATH}/share/man"' >> ~/.bashrc

WORKDIR /root

CMD ["/bin/bash"]

# podman build -t gentoo -f Dockerfile --security-opt=seccomp=/collab/usr/gapps/lcweg/containers/profiles/chown.json --build-arg="CUSTOM_CERT=./tls-ca-bundle.crt"

