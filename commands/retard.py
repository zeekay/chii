from chii import config, command

BRAIN = config['retard_brain']
CHATTINESS = 0
WORD_COUNT = 10
WORD_MAX = 1000
SENTENCE_SEPS = ('. ', '! ', '? ', '\n')

if BRAIN:
    import random, re, os
    from collections import defaultdict

    class MarkovChain:
        chain = defaultdict(list)

        def add_to_brain(self, line, write_to_file=False):
            if write_to_file:
                with open(BRAIN, 'a') as f:
                    f.write(line + '\n')
            w1 = w2 = "\n"
            for word in line.split(' '):
                self.chain[(w1, w2)].append(word)
                w1, w2 = w2, word
            self.chain[w1, w2].append('\n')

        def get_key(self, msg=None):
            if msg and len(msg.split()) > 1:
                words = msg.split()
                w1, w2 = words[0:2]
                for word in words:
                    if self.chain[(w1, w2)] != []:
                        return w1, w2
                    w1, w2 = w2, word
            return random.choice(self.chain.keys())

        def generate_sentence(self, msg):
            sentence = ''
            w1, w2 = self.get_key(msg)
            for i in xrange(WORD_MAX):
                try:
                    word = random.choice(self.chain[(w1, w2)])
                except IndexError:
                    word = random.choice(self.chain[self.get_key()])
                word = word.strip()
                if not word:
                    break
                sentence = ' '.join((sentence, word))
                w1, w2 = w2, word
            if len(sentence) < 20:
                return self.generate_sentence(None)
            return sentence

    @command
    def retard(self, channel, nick, host, *args):
        msg = ' '.join(args)
        def clean_sentence(sentence):
            sentence = sentence.replace('"', '')
            if sentence[-1] in (',', ';'):
                sentence = sentence[:-1]
            if sentence[-1] not in ('!', '.', '?'):
                sentence += '.'
            return sentence.upper()

        prefix = "%s:" % nick
        markov_chain.add_to_brain(msg, write_to_file=True)
        return prefix + clean_sentence(markov_chain.generate_sentence(msg))

    markov_chain = MarkovChain()

    if os.path.exists(BRAIN):
        with open(BRAIN) as f:
            for line in f.readlines():
                markov_chain.add_to_brain(line)
        print 'Retard Brain Loaded'
