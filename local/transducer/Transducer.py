#!/usr/bin/python

import math
import sys
import os

class Grapheme:
    def __init__(self,name,emissions,lam=0.01):
        ''' 
            Constructor for a Grapheme HMM. Specify the set of possible emissions, and 
            an add-1 smoothing weight lam for the counters.
            
            Inputs:
                emissions -- dictionary of emissions
                lam       -- add-1 smoothing weight for arc counters
                
        '''
        # A is the transition matrix.
        # There are 3 arcs:
        # a11, a12, q12
        self.name = name
        self.A = {'a11':0.1, 'a12':0.8, 'q12':0.1}
        
        # B is the observation matrix.
        # There are O possible observations per emitting arc.
        # b11, b12
        self.B = {e:{'a11':val, 'a12':val} for e,val in emissions.iteritems()}
        
        # c_t is are the arc counters
        self.c_t = {'a11':lam, 'a12':lam, 'q12':lam}
        
        # c_ty is the observation arc counters
        self.c_ty = {e:{'a11':lam, 'a12':lam} for e in emissions.iterkeys()}
        self.emissions = emissions
        self.lam = lam
        
    def reset_counters(self):
        self.c_t ={'a11':self.lam, 'a12':self.lam, 'q12':self.lam}
        self.c_ty = {e:{'a11':self.lam, 'a12':self.lam} for e in self.emissions.iterkeys()}

    def update(self):
        # Get the total count of outgoing arcs for each state. In this case there
        # is only 1 starting state though.
        total_count = sum(self.c_t.itervalues())
        
        self.A = {arc: count/total_count for arc,count in self.c_t.iteritems()}
        self.B = { e : 
                      { arc : count/(self.c_t[arc] + (self.lam * (len(self.emissions.keys()) - 1))) 
                           for arc,count in arcs.iteritems() 
                      } for e,arcs in self.c_ty.iteritems()    
                 }
        
        self.reset_counters()
           

class Utterance:
    def __init__(self,utterance_id,utterance,graphemes):
        '''
            Constructure for utterance HMM. It defines the way that individual
            Grapheme objects (HMMs) can be concatenated together to perform
            utterance level training.
        '''
        self.utterance_id = utterance_id
        self.model = utterance.split(" ")
        self.G = graphemes
        for u in self.model:
            try:
                if(self.G[u]):
                    pass
            except KeyError:
                print("Utterace contains graphemes that are not in the grapheme list provided.")
                sys.exit(1)
    
    def do_forward(self,seq):
        # Initialize a few things
        trellis_stages = len(seq) + 1
        number_of_states = len(self.model) + 1
        alpha = [[0.0 for i in range(number_of_states)] for t in range(trellis_stages)]
        alpha[0][0] = 1.0
        
        Q = [0.0 for t in range(trellis_stages)]
        Q[0] = 1.0
        
        # This makes life easier
        seq = ['0'] + seq
        
        # Start sweeping through the trellis and accumulating forward probabilities
        for t in range(1,trellis_stages):
            o = seq[t]
            
            # Sweep through each state
            for s in range(number_of_states):
                if s == 0:
                    alpha[t][s] = alpha[t-1][s] * self.G[self.model[s]].A['a11'] * self.G[self.model[s]].B[o]['a11']
                elif s == number_of_states - 1:
                    alpha[t][s] = alpha[t-1][s-1] * self.G[self.model[s-1]].A['a12'] * self.G[self.model[s-1]].B[o]['a12']
                    if t != (trellis_stages-1):
                        alpha[t][s] += alpha[t-1][s-1] * self.G[self.model[s-1]].A['q12']
                else:
                    alpha[t][s] = alpha[t-1][s] * self.G[self.model[s]].A['a11'] * self.G[self.model[s]].B[o]['a11'] \
                                + alpha[t-1][s-1] * self.G[self.model[s-1]].A['a12'] * self.G[self.model[s-1]].B[o]['a12']
                    if t != (trellis_stages-1):
                        alpha[t][s] += alpha[t][s-1] * self.G[self.model[s-1]].A['q12']
                            
            Q[t] = sum(alpha[t])
            alpha[t][:] = [v/Q[t] for v in alpha[t]]
        
        return alpha,Q,sum([math.log(i) for i in Q])
    
    def do_backward(self,seq,Q=None,alpha=None):
        trellis_stages = len(seq) + 1
        number_of_states = len(self.model) + 1
        beta = [[0.0 for i in range(number_of_states)] for t in range(trellis_stages)]
        beta[-1] = [ 1.0 for i in beta[-1]]
        
        if not Q:
            Q = [0.0 for t in range(trellis_stages)]
            Q[-1] = 1.0
        
        # This makes life easier
        seq = ['0'] + seq
        
        # Start sweeping through the trellis and accumulating backward probabilities
        for t in range(trellis_stages-2,-1,-1):
            o = seq[t+1]
            
            # Sweep through each state
            for s in range(number_of_states-1,-1,-1):
                if s == number_of_states-1:
                    beta[t][s] = 0.0
                else:
                    beta[t][s] = beta[t+1][s]*self.G[self.model[s]].A['a11']*self.G[self.model[s]].B[o]['a11'] \
                                + beta[t+1][s+1]*self.G[self.model[s]].A['a12']*self.G[self.model[s]].B[o]['a12']
                    if t != 0:
                        beta[t][s] += beta[t][s+1]*self.G[self.model[s]].A['q12']
            
            if Q[-1] == 1.0:
                Q[t] = sum(beta[t])

            beta[t][:] = [v/Q[t] for v in beta[t]]
            
            if alpha:
                self.update_arc_counts(alpha[t], beta[t+1], o, beta[t], Q[t])
        
        # The Q, and LL terms are only useful for debugging when Q does not come from 
        # the forward pass
        return beta,Q,(sum([math.log(i) for i in Q]) + math.log(beta[0][0]))
    
    def update_arc_counts(self, alpha_t, beta_t_plus_1, o, beta_t, Q):
     
        # Update all possible arc counts
        number_of_states = len(alpha_t)
        
        for s1 in range(number_of_states-1):
            # Self arc
            p_t = alpha_t[s1] * self.G[self.model[s1]].A['a11'] \
                * self.G[self.model[s1]].B[o]['a11'] * beta_t_plus_1[s1]
                
            self.G[self.model[s1]].c_ty[o]['a11'] += p_t
            self.G[self.model[s1]].c_t['a11'] += p_t
            
            # Transition arc
            p_t = alpha_t[s1] * self.G[self.model[s1]].A['a12'] \
                * self.G[self.model[s1]].B[o]['a12'] * beta_t_plus_1[s1+1]
            
            self.G[self.model[s1]].c_ty[o]['a12'] += p_t
            self.G[self.model[s1]].c_t['a12'] += p_t
    
            # Null arc
            self.G[self.model[s1]].c_t['q12'] += alpha_t[s1] * self.G[self.model[s1]].A['q12'] * beta_t[s1+1] * Q
    
    def train_sequence(self,seq):
        alpha,Q,LL = self.do_forward(seq)
        beta,_,_ = self.do_backward(seq, Q=Q, alpha=alpha)
        return LL
